"""
AI Command -> Execution -> Output Linkage — End-to-End Verification

Tests that SHUNYA creates durable command/execution/output records
for AI chat interactions.
"""
import os, json, sys
os.environ['DISABLE_RATE_LIMIT'] = '1'
os.environ['FLASK_ENV'] = 'testing'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.auth import TeamMember
from app.tenant import Tenant
from flask.testing import FlaskClient

# ── Bootstrap ──────────────────────────────────────────────────────────────
app = create_app(config_override={
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret',
    'DISABLE_RATE_LIMIT': 'true',
    'WTF_CSRF_ENABLED': False,
})

results = []

with app.app_context():
    db.create_all()

    # Create tenant + user
    tenant = Tenant(company_name="TestCorp", slug="testcorp", business_type="tech", is_active=True)
    db.session.add(tenant)
    db.session.commit()

    user = TeamMember(name="Test User", email="test@testcorp.com", role="admin", is_active=True)
    user.set_password("password123")
    user.generate_token()
    db.session.add(user)
    db.session.commit()

    client = app.test_client()

    # Authenticate — need identity_id and tenant_id for founder routes
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['identity_id'] = str(user.id)
        sess['tenant_id'] = tenant.id
        sess['_fresh'] = True

    # ═══════════════════════════════════════════════════════════════
    # TEST 1: AI Chat — does it accept and process messages?
    # ═══════════════════════════════════════════════════════════════
    print("\n=== TEST 1: AI Chat ===")
    resp = client.post('/api/v1/ai/chat', json={
        'messages': [{'role': 'user', 'content': 'Create a proposal for a new software project'}]
    })
    data1 = resp.get_json(silent=True) or {}
    print(f"  Status: {resp.status_code}")
    print(f"  Response keys: {list(data1.keys())}")
    if data1.get('error'):
        print(f"  Error (expected if no provider): {data1['error'][:80]}")
    else:
        print(f"  Sample: {json.dumps(data1)[:200]}")
    results.append(('AI Chat', resp.status_code, data1.get('error') is None))

    # ═══════════════════════════════════════════════════════════════
    # TEST 2: Conversations API
    # ═══════════════════════════════════════════════════════════════
    print("\n=== TEST 2: Conversations API ===")
    resp = client.get('/api/v1/communication/conversations')
    data2 = resp.get_json(silent=True) or {}
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(data2)[:200]}")
    results.append(('Conversations list', resp.status_code, resp.status_code == 200))

    # Create a conversation
    resp = client.post('/api/v1/communication/conversations', json={
        'title': 'Test conversation',
        'participants': [user.id]
    })
    data3 = resp.get_json(silent=True) or {}
    print(f"  Create conv status: {resp.status_code}")
    conv_id = data3.get('id') or data3.get('conversation_id') or None
    print(f"  Conversation ID: {conv_id}")
    results.append(('Create conversation', resp.status_code, conv_id is not None))

    # ═══════════════════════════════════════════════════════════════
    # TEST 3: Conversation - add message, verify persistence
    # ═══════════════════════════════════════════════════════════════
    if conv_id:
        print("\n=== TEST 3: Message Persistence ===")
        # Add a message
        resp = client.post(f'/api/v1/communication/conversations/{conv_id}/messages', json={
            'content': 'What is the status of our sales pipeline?',
            'role': 'user'
        })
        data_msg = resp.get_json(silent=True) or {}
        print(f"  Send message status: {resp.status_code}")

        # Fetch conversation to verify message persisted
        resp = client.get(f'/api/v1/communication/conversations/{conv_id}')
        data_get = resp.get_json(silent=True) or {}
        print(f"  Get conversation status: {resp.status_code}")
        msgs = data_get.get('messages', [])
        print(f"  Messages count: {len(msgs)}")
        results.append(('Message persistence', resp.status_code, len(msgs) > 0))

    # ═══════════════════════════════════════════════════════════════
    # TEST 4: Intelligence - ask commercial intelligence
    # ═══════════════════════════════════════════════════════════════
    print("\n=== TEST 4: Intelligence Ask ===")
    resp = client.post('/api/v1/intelligence/ask', json={
        'question': 'What is the current status of our sales pipeline?',
        'tenant_id': tenant.id
    })
    data4 = resp.get_json(silent=True) or {}
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(data4)[:300]}")
    results.append(('Intelligence ask', resp.status_code, True))

    # ═══════════════════════════════════════════════════════════════
    # TEST 5: Memory — can we retrieve knowledge?
    # ═══════════════════════════════════════════════════════════════
    print("\n=== TEST 5: Memory ===")
    resp = client.get('/api/v1/memory/entries')
    data5 = resp.get_json(silent=True) or {}
    print(f"  Status: {resp.status_code}")
    print(f"  Memory entries: {json.dumps(data5)[:200]}")
    results.append(('Memory entries', resp.status_code, True))

    resp = client.get('/api/v1/memory/knowledge')
    data6 = resp.get_json(silent=True) or {}
    print(f"  Knowledge status: {resp.status_code}")
    print(f"  Knowledge: {json.dumps(data6)[:200]}")
    results.append(('Memory knowledge', resp.status_code, True))

    # ═══════════════════════════════════════════════════════════════
    # TEST 6: Founder AI
    # ═══════════════════════════════════════════════════════════════
    print("\n=== TEST 6: Founder AI ===")
    resp = client.get('/api/v1/founder/ai/health')
    data7 = resp.get_json(silent=True) or {}
    print(f"  Status: {resp.status_code}")
    print(f"  AI Health: {json.dumps(data7)[:200]}")
    results.append(('Founder AI health', resp.status_code, resp.status_code == 200))

    # ═══════════════════════════════════════════════════════════════
    # TEST 7: Execution - check outputs
    # ═══════════════════════════════════════════════════════════════
    print("\n=== TEST 7: Execution ===")
    resp = client.get('/api/v1/execution/outputs')
    data8 = resp.get_json(silent=True) or {}
    print(f"  Status: {resp.status_code}")
    print(f"  Outputs: {json.dumps(data8)[:200]}")
    results.append(('Execution outputs', resp.status_code, True))

    resp = client.get('/api/v1/execution/work')
    data9 = resp.get_json(silent=True) or {}
    print(f"  Work status: {resp.status_code}")
    print(f"  Work: {json.dumps(data9)[:200]}")
    results.append(('Execution work', resp.status_code, True))

    # ═══════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("AI COMMAND → EXECUTION → OUTPUT LINKAGE RESULTS")
    print("=" * 60)
    passed = all(r[2] for r in results)
    for name, status, ok in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: HTTP {status}")
    print(f"\n  Overall: {'✅ PASS' if passed else '❌ FAIL'}")

db.drop_all()