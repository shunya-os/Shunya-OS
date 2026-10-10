"""Test E4 flow directly."""
import os
os.environ['SHUNYA_AI_PROVIDERS'] = 'local'

from app import create_app, db
app = create_app({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret',
    'WTF_CSRF_ENABLED': False,
    'DISABLE_RATE_LIMIT': True,
})
with app.app_context():
    db.create_all()
    from core.intelligence_runtime.integration import ask, ensure_runtime
    ensure_runtime()
    res = ask(
        query='confirmed: create customer E4 Sunrise Travels',
        session_id='e4_test',
        identity_id='sid_e4_test',
        tenant_id='7',
    )
    print('CONTENT:', (res.get('content') or '')[:500])
    print('STATUS:', res.get('status', 'N/A'))
    print('KEYS:', list(res.keys()))
    import json
    print('FULL:', json.dumps(res, default=str)[:2000])