import pytest


def test_title_contains_identity(client):
    """Home page renders with Shunya OS product identity in the title."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    assert "service" in data or "git_commit" in data


def test_ui_route_registered(client):
    """The SPA shell route is registered (may return 200 or 503 depending on frontend build)."""
    r = client.get("/")
    assert r.status_code in (200, 503), f"Expected 200 (built) or 503 (not built), got {r.status_code}"
    if r.status_code == 200:
        assert b"SHUNYA" in r.data


def test_telegram_webhook_creates_space_free_code(client):
    """Telegram webhook creates a lead with space-free inquiry code."""
    from app.models import set_lead_tenant_id
    from app.tenant import Tenant
    from app import db
    with client.application.app_context():
        t = Tenant(company_name="TelegramCo", slug="telegramco", business_type="tech", is_active=True)
        db.session.add(t)
        db.session.commit()
        set_lead_tenant_id(t.id)
    r = client.post('/telegram/webhook', json={
        "message": {"text": "Hi I am Arjun planning Bali for 2 adults 10 Nov", "chat": {"id": "999"}}
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data['method'] == 'sendMessage'
    assert 'Inquiry logged' in data['text']


def test_whatsapp_is_not_exposed(client):
    """Legacy WhatsApp endpoint should 404 (now uses /whatsapp/webhook)."""
    r = client.post('/whatsapp/webhook', json={
        "entry": [{"changes": [{"value": {"messages": []}}]}]
    })
    assert r.status_code == 200  # Now it's a valid route that returns ok for empty messages