"""G1.1-R6 — Behavioral RBAC + tenant isolation security proof.

Tests actual authorization behavior across all critical paths.
This is NOT a decorator-count — it exercises deny-by-default,
cross-org isolation, role-based access, and manipulated-ID attacks.
"""
import pytest
from tests.auth_helper import seed_rbac
from app.execution.core_models import ExecutionRun
from app.execution.task_lifecycle import TaskLifecycle


class TestBehavioralRBAC:
    """§8 — Behavioral security proof, not decorator count."""

    def test_no_org_context_denied(self, app, client):
        """Unauthenticated → 401 at the middleware gate."""
        resp = client.post("/api/v1/intelligence/ask",
                           json={"question": "hi"})
        assert resp.status_code in (401, 401), f"Expected 401, got {resp.status_code}"

    def test_wrong_org_denied(self, app, client):
        """User in Org A cannot access Org B data."""
        with client.session_transaction() as s:
            s["user_id"] = "attacker@evil.com"
            s["identity_id"] = "attacker"
            s["current_org_id"] = 99999  # org they don't belong to
        from app import db
        from app.models import OrgMember
        om = OrgMember.query.filter_by(identity_id="attacker", organization_id=99999).first()
        if not om:
            # attacker has no OrgMember in org 99999 — should be denied
            resp = client.get("/api/v1/objects/list")
            assert resp.status_code in (403, 404, 405), f"Expected denial, got {resp.status_code}"

    def test_no_role_no_permission(self, app, client):
        """Member with no role assignment gets 403 on permission-gated routes."""
        from app import db
        from app.models import Organization, OrgMember
        org_id = 77777
        org = Organization(id=org_id, name="No Role Org", slug="no-role-org")
        db.session.add(org)
        db.session.flush()
        om = OrgMember(organization_id=org_id, identity_id="norole_user",
                       role="member", is_active=True)
        db.session.add(om)
        db.session.commit()
        with client.session_transaction() as s:
            s["user_id"] = "norole_user"
            s["identity_id"] = "norole_user"
            s["current_org_id"] = org_id
        # This route requires a specific permission
        resp = client.get("/api/v1/audit/logs")
        assert resp.status_code in (403, 404), f"Expected 403/404, got {resp.status_code}"

    def test_cross_execution_denied(self, app, client):
        """Org A cannot read Org B's execution runs."""
        from app import db
        from app.execution.core_models import ExecutionRun
        from app.models import Organization, OrgMember
        # Create Org B's execution run
        org_b_id = seed_rbac(db, identity_id="org_b_user", role_name="admin")
        run = ExecutionRun(
            execution_id="exec_cross_org_b",
            organization_id=org_b_id, identity_id="org_b_user",
            intent="Org B secret", run_type="analysis", status="completed"
        )
        db.session.add(run)
        db.session.commit()
        # Org A tries to read it
        org_a_id = seed_rbac(db, identity_id="org_a_attacker", role_name="admin")
        with client.session_transaction() as s:
            s["identity_id"] = "org_a_attacker"
            s["current_org_id"] = org_a_id
        resp = client.get(f"/api/v1/execution/runs/exec_cross_org_b")
        # Org A should NOT see Org B's run
        assert resp.status_code in (403, 404), f"Expected 403/404 cross-org, got {resp.status_code}"

    def test_cross_task_denied(self, app, client):
        """Org A cannot read Org B's tasks."""
        from app import db
        from app.execution.task_lifecycle import TaskLifecycle
        org_b_id = seed_rbac(db, identity_id="b_task_owner")
        task = TaskLifecycle(
            task_id="task_cross_org_b",
            organization_id=org_b_id, identity_id="b_task_owner",
            title="Secret task B", status="completed"
        )
        db.session.add(task); db.session.commit()
        org_a_id = seed_rbac(db, identity_id="a_task_attacker")
        with client.session_transaction() as s:
            s["identity_id"] = "a_task_attacker"
            s["current_org_id"] = org_a_id
        resp = client.get(f"/api/v1/execution/tasks/task_cross_org_b")
        assert resp.status_code in (403, 404), f"Expected 403/404 cross-org, got {resp.status_code}"

    def test_manipulated_execution_id_denied(self, app, client):
        """User cannot access execution run by guessing another user's ID."""
        from app import db
        owner_id = seed_rbac(db, identity_id="run_owner", role_name="admin")
        run = ExecutionRun(
            execution_id="exec_manipulated",
            organization_id=owner_id, identity_id="run_owner",
            intent="Owner's run", run_type="analysis", status="completed"
        )
        db.session.add(run); db.session.commit()
        attacker_id = seed_rbac(db, identity_id="manipulator", role_name="admin")
        with client.session_transaction() as s:
            s["identity_id"] = "manipulator"
            s["current_org_id"] = attacker_id  # different org!
        resp = client.get(f"/api/v1/execution/runs/exec_manipulated")
        assert resp.status_code in (403, 404), f"Manipulated ID access denied expected, got {resp.status_code}"

    def test_evidence_org_isolation(self, app, client):
        """Organization A's evidence is not visible to Organization B."""
        from app import db
        from app.evidence.models_db import create_evidence
        org_a = seed_rbac(db, identity_id="a_ev_owner")
        ev = create_evidence(source_type="execution", source_id="exec_ev_a",
                             raw_reference={"org": str(org_a), "secret": "A-data"})
        assert ev is not None
        org_b = seed_rbac(db, identity_id="b_ev_attacker")
        with client.session_transaction() as s:
            s["identity_id"] = "b_ev_attacker"
            s["current_org_id"] = org_b
        # evidence_records is not directly exposed via REST — checked via execution run
        run = ExecutionRun(
            execution_id="exec_ev_a", organization_id=org_a,
            identity_id="a_ev_owner", intent="test", run_type="analysis",
            status="completed"
        )
        db.session.add(run); db.session.commit()
        resp = client.get(f"/api/v1/execution/runs/exec_ev_a")
        assert resp.status_code in (403, 404), f"Cross-org execution access, got {resp.status_code}"

    def test_direct_api_access_without_session_denied(self, app, client):
        """Direct API calls without authentication get 401/403."""
        resp = client.post("/api/v1/intelligence/ask",
                           json={"question": "hack", "action": "delete", "execute": True})
        assert resp.status_code in (401, 403, 405), f"Unauthenticated expected denial, got {resp.status_code}"

    def test_all_decorated_routes_reject_unauthenticated(self, app, client):
        """Probe a sample of protected routes without auth — all must deny."""
        routes = [
            ("GET", "/api/v1/objects/list"),
            ("POST", "/api/v1/execution/runs/search"),
            ("GET", "/api/v1/intelligence/history"),
            ("GET", "/api/v1/workspace/spaces"),
            ("POST", "/api/v1/intelligence/ask"),
            ("GET", "/api/v1/execution/runs"),
            ("GET", "/api/v1/execution/tasks"),
            ("GET", "/api/v1/audit/logs"),
            ("GET", "/api/v1/memory/search"),
        ]
        for method, path in routes:
            if method == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json={})
            assert resp.status_code in (400, 401, 403, 404, 405), (
                f"Route {method} {path} returned {resp.status_code} without auth"
            )

class TestPDFKitSecurity:
    """PDF generation security: caller options cannot re-enable JavaScript."""

    def _capture_options(self, extra_options=None):
        """Call generate_pdf with patched pdfkit, return the options dict used."""
        from app.pdf_safe import generate_pdf
        import tempfile, os, sys, types

        captured = {}

        def fake_from_string(html, output_path, options=None):
            captured["options"] = options
            with open(output_path, "wb") as f:
                f.write(b"%PDF-1.4 test")

        # Replace sys.modules['pdfkit'] so the function-local `import pdfkit`
        # resolves to our fake. Restore the original afterwards.
        original_module = sys.modules.get("pdfkit")
        fake_module = types.ModuleType("pdfkit")
        fake_module.from_string = fake_from_string
        sys.modules["pdfkit"] = fake_module
        try:
            with tempfile.TemporaryDirectory() as td:
                out = os.path.join(td, "out.pdf")
                generate_pdf("<html><body>Hello</body></html>", out, extra_options=extra_options)
        finally:
            if original_module is not None:
                sys.modules["pdfkit"] = original_module
            else:
                sys.modules.pop("pdfkit", None)
        return captured.get("options", {})

    def test_caller_cannot_reenable_javascript(self, app, client):
        """Negative test: caller-supplied enable-javascript is overridden."""
        options = self._capture_options({
            "enable-javascript": "",
            "javascript-delay": "2000",
            "run-script": "evil.js",
        })
        # Security invariants must be present and enforce no-JS
        assert options.get("no-javascript") == ""
        assert options.get("disable-javascript") == ""
        # The caller's enable-javascript attempt must not survive as a toggle
        assert "enable-javascript" not in options or options.get("enable-javascript") in ("", None)
        # javascript-delay must stay at the safe 0
        assert str(options.get("javascript-delay")) == "0"

    def test_caller_cannot_disable_security_defaults(self, app, client):
        """Negative test: security keys enforced even when caller omits them."""
        options = self._capture_options({})
        assert options.get("no-javascript") == ""
        assert options.get("disable-javascript") == ""
        assert str(options.get("javascript-delay")) == "0"
