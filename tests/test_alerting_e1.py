"""E1 — operational alerting: detection, dedup, delivery handling, recovery.

The full lifecycle is exercised with the delivery channel monkeypatched
(never a real email in tests) and the e2e proof happens live in production
via POST /api/v1/system/alerts/test.
"""
import time

import pytest


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "e1-alerting",
    })
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def fresh_engine(app):
    """Reset the singleton engine state between tests (flood windows etc.)."""
    from app.alerting.service import get_alert_engine, AlertEngine
    from app import db
    from app.alerting.models import AlertEvent
    engine = get_alert_engine()
    engine._flood_windows = {}
    engine._recovery_checked_at = {}
    with app.app_context():
        AlertEvent.query.delete()
        db.session.commit()
        yield engine
        AlertEvent.query.delete()
        db.session.commit()


@pytest.fixture(autouse=True)
def fake_email(app, monkeypatch):
    """Replace the delivery channel with a deterministic recorder."""
    from app.alerting import service as alerting_service
    calls = {"deliveries": []}

    def _fake_deliver(self, recipient, subject, body):
        calls["deliveries"].append({"recipient": recipient, "subject": subject})
        return {"status": "accepted", "channel": "email"}

    monkeypatch.setattr(alerting_service.AlertEngine, "_deliver", _fake_deliver)
    monkeypatch.setattr(alerting_service, "DEFAULT_RECIPIENT", "ops@test.com")
    return calls


def _login_admin(client, identity_id="admin@test.com"):
    from tests.auth_helper import seed_rbac
    from app import db
    with client.application.app_context():
        org_id = seed_rbac(db, identity_id=identity_id, role_name="owner")
    with client.session_transaction() as sess:
        sess["identity_id"] = identity_id
        sess["user_id"] = identity_id
        sess["current_org_id"] = org_id
        sess["_fresh"] = True
    return org_id


class TestFloodDetection:
    def test_below_threshold_no_alert(self, app, fresh_engine, fake_email):
        from app.alerting.service import FAILURE_FLOOD_THRESHOLD
        from app.alerting.models import AlertEvent
        engine = fresh_engine
        for _ in range(FAILURE_FLOOD_THRESHOLD - 1):
            engine.ingest_failure("/api/v1/x", "SomeException")
        with app.app_context():
            assert AlertEvent.query.count() == 0

    def test_flood_crosses_threshold_fires_once(self, app, fresh_engine, fake_email):
        from app.alerting.service import FAILURE_FLOOD_THRESHOLD
        from app.alerting.models import AlertEvent
        engine = fresh_engine
        for _ in range(FAILURE_FLOOD_THRESHOLD):
            engine.ingest_failure("/api/v1/x", "SomeException")
        with app.app_context():
            events = AlertEvent.query.all()
            assert len(events) == 1
            assert events[0].rule == "http_5xx"
            assert events[0].status == "active"
            assert events[0].delivery_state == "delivered"
            assert len(fake_email["deliveries"]) == 1

    def test_flood_dedup_no_second_delivery_within_cooldown(self, app, fresh_engine, fake_email):
        from app.alerting.service import FAILURE_FLOOD_THRESHOLD
        engine = fresh_engine
        for _ in range(FAILURE_FLOOD_THRESHOLD):
            engine.ingest_failure("/api/v1/x", "SomeException")
        # Above threshold again immediately: appended, no new email.
        for _ in range(FAILURE_FLOOD_THRESHOLD):
            engine.ingest_failure("/api/v1/x", "SomeException")
        with app.app_context():
            from app.alerting.models import AlertEvent
            assert AlertEvent.query.filter_by(status="active").count() == 1
        assert len(fake_email["deliveries"]) == 1

    def test_db_error_classified_p1(self, app, fresh_engine, fake_email):
        from app.alerting.service import FAILURE_FLOOD_THRESHOLD
        engine = fresh_engine
        for _ in range(FAILURE_FLOOD_THRESHOLD):
            engine.ingest_failure("/api/v1/query", "sqlalchemy.exc.OperationalError")
        with app.app_context():
            from app.alerting.models import AlertEvent
            event = AlertEvent.query.first()
            assert event.rule == "db_error"
            assert event.severity == "P1"


class TestDeliveryHandling:
    def test_unconfigured_channel_recorded_not_delivered(self, app, fresh_engine, monkeypatch):
        from app.alerting import service as alerting_service
        engine = fresh_engine
        monkeypatch.setattr(alerting_service, "DEFAULT_RECIPIENT", "")
        result = engine.fire_test_alert()
        assert result["fired"] is True
        with app.app_context():
            from app.alerting.models import AlertEvent
            event = AlertEvent.query.filter_by(rule="test_alert").first()
            assert event.delivery_state == "unconfigured"

    def test_delivery_failure_retries_then_marks_failed(self, app, fresh_engine, monkeypatch):
        from app.alerting import service as alerting_service
        engine = fresh_engine
        attempts = {"n": 0}

        def _failing_deliver(self, recipient, subject, body):
            attempts["n"] += 1
            raise RuntimeError("provider down")

        monkeypatch.setattr(alerting_service.AlertEngine, "_deliver", _failing_deliver)
        engine.fire_test_alert()
        assert attempts["n"] == alerting_service.MAX_DELIVERY_ATTEMPTS
        with app.app_context():
            from app.alerting.models import AlertEvent
            event = AlertEvent.query.filter_by(rule="test_alert").first()
            assert event.delivery_state == "failed"
            assert event.details.get("delivery_attempts") == alerting_service.MAX_DELIVERY_ATTEMPTS

    def test_delivery_failure_never_raises_into_caller(self, app, fresh_engine, monkeypatch):
        from app.alerting import service as alerting_service
        engine = fresh_engine
        monkeypatch.setattr(
            alerting_service.AlertEngine, "_deliver",
            lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        # Must NOT raise.
        result = engine.fire_test_alert()
        assert result["fired"] is True


class TestRecoveryVerification:
    def test_recovery_marks_event_and_delivers_resolution(self, app, fresh_engine, fake_email):
        from app.alerting import service as alerting_service
        from app.alerting.models import AlertEvent
        engine = fresh_engine
        with app.app_context():
            from datetime import datetime, timedelta
            ev = AlertEvent(
                rule="http_5xx", alert_key="/api/v1/x:SomeException",
                severity="P2", status="active", subject="[SHUNYA] http_5xx flood on /x",
                body="flood", first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow() - timedelta(seconds=alerting_service.RECOVERY_QUIET_SECONDS + 60),
                occurrences=6, delivery_state="delivered",
            )
            from app import db
            db.session.add(ev)
            db.session.commit()
        recovered = engine.check_recovery()
        assert recovered == 1
        with app.app_context():
            ev2 = AlertEvent.query.filter_by(alert_key="/api/v1/x:SomeException").first()
            assert ev2.status == "recovered"
            assert ev2.recovered_at is not None
        # Resolution message delivered (fake channel records 2nd delivery).
        assert any("RECOVERED" in d["subject"] for d in fake_email["deliveries"])

    def test_active_failures_postpone_recovery(self, app, fresh_engine, fake_email):
        from app.alerting.service import RECOVERY_QUIET_SECONDS
        from app.alerting.models import AlertEvent
        engine = fresh_engine
        # Recent failure keeps the rule in the "recently active" set.
        engine.ingest_failure("/api/v1/y", "SomeException")
        with app.app_context():
            from datetime import datetime, timedelta
            from app import db
            ev = AlertEvent(
                rule="http_5xx", alert_key="/api/v1/old:x", severity="P2",
                status="active", subject="old", body="old",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow() - timedelta(seconds=RECOVERY_QUIET_SECONDS + 60),
                occurrences=9, delivery_state="delivered",
            )
            db.session.add(ev)
            db.session.commit()
        recovered = engine.check_recovery()
        assert recovered == 0


class TestEndpoints:
    def test_alerts_require_admin(self, client, app):
        resp = client.get("/api/v1/system/alerts")
        assert resp.status_code in (401, 403)

    def test_admin_lists_alerts(self, client, app, fresh_engine, fake_email):
        from tests.auth_helper import seed_rbac
        with app.app_context():
            _login_admin(client)
        resp = client.get("/api/v1/system/alerts")
        assert resp.status_code == 200
        assert "alerts" in resp.get_json()

    def test_test_alert_endpoint_fires_e2e(self, client, app, fresh_engine, fake_email):
        _login_admin(client)
        resp = client.post("/api/v1/system/alerts/test", json={})
        assert resp.status_code == 200
        assert resp.get_json()["fired"] is True
        assert len(fake_email["deliveries"]) == 1

    def test_simulate_endpoint_drives_detection(self, client, app, fresh_engine, fake_email):
        _login_admin(client)
        resp = client.post("/api/v1/system/alerts/simulate", json={"count": 3})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["active_alerts"] >= 1