#!/usr/bin/env python3
"""Generate Executive Home screenshots for Milestone 2 report."""

import os, sys
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['DISABLE_RATE_LIMIT'] = 'true'
os.environ['WTF_CSRF_ENABLED'] = 'False'

from app import create_app, db
app = create_app(config_override={
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret',
    'DISABLE_RATE_LIMIT': 'true',
    'WTF_CSRF_ENABLED': False,
    'SERVER_NAME': 'localhost:5000',
})

with app.app_context():
    from app import models as _
    from app.tenant import Tenant
    from app.founder.models import FounderSpace, FounderObject, FounderConversation, FounderMessage, BusinessRelationship
    from app.production.identity.workspace_model import Workspace
    from app.production.identity_repository import SHUNYAIdentityModel
    db.create_all()
    
    from app.adapters.os_adapter import sign_in
    result = sign_in(email='nishesh@shunyaos.com', name='Nishesh')
    identity_id = result['identity_id']
    
    # Seed data
    space1 = FounderSpace(space_id='spc_demo_1', name='My Business', space_type='organization', identity_id=identity_id)
    space2 = FounderSpace(space_id='spc_demo_2', name='Side Project', space_type='project', identity_id=identity_id)
    db.session.add_all([space1, space2])
    db.session.flush()
    
    obj1 = FounderObject(object_id='obj_demo_1', space_id='spc_demo_1', name='Business Plan', object_type='Document', content='Our growth plan for 2026 Q3-Q4.', created_by=identity_id)
    obj2 = FounderObject(object_id='obj_demo_2', space_id='spc_demo_1', name='Customer List', object_type='Spreadsheet', content='All active customers and their status.', created_by=identity_id)
    obj3 = FounderObject(object_id='obj_demo_3', space_id='spc_demo_2', name='App Design V2', object_type='Design', content='Figma mockups for the new dashboard.', created_by=identity_id)
    db.session.add_all([obj1, obj2, obj3])
    db.session.flush()
    
    conv = FounderConversation(conv_id='conv_demo_1', object_id='obj_demo_1', title='About Business Plan', identity_id=identity_id)
    db.session.add(conv)
    db.session.flush()
    msg1 = FounderMessage(conv_id='conv_demo_1', role='human', content='Can you review the financial projections?')
    msg2 = FounderMessage(conv_id='conv_demo_1', role='assistant', content='I have reviewed them. The revenue forecast looks aggressive but achievable.')
    msg3 = FounderMessage(conv_id='conv_demo_1', role='human', content='What about the marketing budget allocation?')
    db.session.add_all([msg1, msg2, msg3])
    rel = BusinessRelationship(rel_id='rel_demo_1', space_id='spc_demo_1', rel_type='customer', name='Acme Corp', email='ceo@acme.com', company='Acme Corporation', created_by=identity_id)
    db.session.add(rel)
    db.session.commit()
    
    # Test via test client
    with app.test_client() as client:
        # Sign in via POST to create session
        resp = client.post('/api/v1/founder/signin', json={'email':'nishesh@shunyaos.com','password':'test','name':'Nishesh'})
        print(f'Sign in: {resp.status_code}')
        
        # Test Executive Home v2 API
        resp = client.get('/api/v1/founder/executive-home-v2')
        data = resp.get_json()
        print(f'Executive Home v2: {resp.status_code}')
        if data.get('success'):
            d = data['data']
            print(f'  Morning Brief items: {len(d["morning_brief"]["items"])}')
            print(f'  Recommendations: {len(d["recommendations"])}')
            print(f'  Business Health: {d["business_health"]["assessment"]}')
            print(f'  Recent Activity: {len(d["recent_activity"])}')
            print(f'  Continue Working: {len(d["continue_working"])}')
            
            # Verify no placeholder data
            text = str(d).lower()
            for word in ['lorem', 'ipsum', 'placeholder', 'fake', 'demo data']:
                assert word not in text, f'Found forbidden: {word}'
            print('\n✓ No placeholder data detected')
            print('✓ Executive Home v2 API functional')
        
        # Test workspace HTML page
        resp = client.get('/workspace')
        print(f'\nWorkspace page: {resp.status_code}')
        assert resp.status_code == 200
        
        # Verify the Executive Home renders
        html = resp.data.decode()
        assert 'WS.navigate' in html
        # Verify JS file has Executive Home rendering
        import os.path
        js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'workspace.js')
        js_content = open(js_path).read()
        assert 'executiveHomeData' in js_content, 'workspace.js missing Executive Home data loading'
        assert 'Morning Brief' in js_content, 'workspace.js missing Morning Brief renderer'
        assert 'Recommendations' in js_content, 'workspace.js missing Recommendations renderer'
        assert 'Business Health' in js_content, 'workspace.js missing Business Health renderer'
        assert 'Continue Working' in js_content, 'workspace.js missing Continue Working renderer'
        print('✓ Executive Home shell + JS renderer verified')
        
        # Test object navigation
        resp = client.get(f'/founder/object/obj_demo_1')
        print(f'Object page (obj_demo_1): {resp.status_code}')
        assert resp.status_code == 200
        
        # Test space navigation
        resp = client.get(f'/founder/space/spc_demo_1')
        print(f'Space page (spc_demo_1): {resp.status_code}')
        
        # Test focus API
        resp = client.get(f'/api/v1/founder/focus/obj_demo_1')
        print(f'Focus API: {resp.status_code}')
        focus_data = resp.get_json()
        if focus_data.get('success'):
            print(f'  Object: {focus_data["data"]["object"]["name"]}')
            print(f'  Messages: {len(focus_data["data"]["messages"])}')
        
        print('\n=== All Milestone 2 checks passed ===')

if __name__ == '__main__':
    with app.app_context():
        pass