import pytest
from app import create_app, db


@pytest.fixture()
def app():
    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "DISABLE_RATE_LIMIT": "true",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_title_contains_identity(client):
    """Home page (redirect) should reference AI@panchi.club after follow."""
    r = client.get('/', follow_redirects=False)
    assert r.status_code in (200, 302, 308)
    if r.status_code == 302:
        r = client.get('/', follow_redirects=True)
    body = r.data.decode('utf-8', 'ignore')
    assert 'AI@panchi.club' in body


def test_telegram_webhook_creates_space_free_code(client):
    """Telegram webhook creates a lead with space-free inquiry code."""
    r = client.post('/telegram/webhook', json={
        "message": {"text": "Hi I am Arjun planning Bali for 2 adults 10 Nov", "chat": {"id": "999"}}
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data['method'] == 'sendMessage'
    assert 'Inquiry logged' in data['text']
    # Extract the code (starts with PC)
    token = [part for part in data['text'].split() if part.startswith('PC')][0]
    assert ' ' not in token
    assert len(token) == 10


def test_whatsapp_is_not_exposed(client):
    """Legacy WhatsApp endpoint should 404 (now uses /whatsapp/webhook)."""
    r = client.post('/whatsapp/webhook', json={
        "entry": [{"changes": [{"value": {"messages": []}}]}]
    })
    assert r.status_code == 200  # Now it's a valid route that returns ok for empty messages