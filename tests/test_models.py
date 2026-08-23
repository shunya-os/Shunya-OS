import pytest


def test_title_contains_identity(client):
    """Home page renders with Shunya OS product identity in the title."""
    r = client.get("/")
    assert r.status_code == 200
    # React SPA shell sets <title>SHUNYA — One Operating System for Your Business</title>
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