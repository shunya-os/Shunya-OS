import pytest
from app import create_app
from app.models import db as _db, Lead

@pytest.fixture()
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

def test_title_contains_identity(client):
    r = client.get('/')
    assert r.status_code in (200, 302, 308)
    body = r.data.decode('utf-8', 'ignore')
    assert 'AI@panchi.club' in body

def test_telegram_webhook_creates_space_free_code(client):
    r = client.post('/telegram/webhook', json={
        "message": {"text": "Hi I am Arjun planning Bali for 2 adults 10 Nov", "chat": {"id": "999"}}
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data['method'] == 'sendMessage'
    assert 'Inquiry logged' in data['text']
    token = [part for part in data['text'].split() if part.startswith('PC')][0]
    assert ' ' not in token
    assert len(token) == 10

def test_whatsapp_is_not_exposed(client):
    r = client.post('/whatsapp/webhook', data={'Body':'x','From':'whatsapp:+1'})
    assert r.status_code == 404
