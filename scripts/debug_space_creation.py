#!/usr/bin/env python3
"""Debug space creation on PostgreSQL."""
import os
os.environ['DATABASE_URL'] = 'postgresql://shunya-deploy:@localhost:5433/shunya_db'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['DISABLE_RATE_LIMIT'] = 'true'
os.environ['WTF_CSRF_ENABLED'] = 'False'

from app import create_app, db
from app.founder.models import FounderSpace, FounderObject

app = create_app(config_override={
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'postgresql://shunya-deploy:@localhost:5433/shunya_db',
    'SECRET_KEY': 'test-secret',
    'DISABLE_RATE_LIMIT': 'true',
    'WTF_CSRF_ENABLED': False,
})

with app.app_context():
    from app import models as _
    from app.tenant import Tenant
    from app.production.identity.workspace_model import Workspace
    from app.production.identity_repository import SHUNYAIdentityModel
    db.create_all()
    print('Tables created')
    
    from app.adapters.os_adapter import sign_in, create_space
    result = sign_in(email='nishesh@shunyaos.com', name='Nishesh')
    iid = result['identity_id']
    print(f'Sign in: {result["success"]}, identity_id: {iid[:24]}')
    
    result2 = create_space(name='My Business', identity_id=iid)
    print(f'Create space result: {result2}')
    
    # Check what the pipeline returned  
    trace = result2.get('trace', [])
    print(f'Pipeline trace ({len(trace)} stages):')
    for t in trace:
        print(f'  [{t["stage"]}] runtime={t["runtime"]} status={t["status"]}')
    
    runtime_results = result2.get('runtime_results', {})
    for stage, res in runtime_results.items():
        print(f'  Stage {stage}: {str(res)[:200]}')
    
    # Check if object_id was created
    oid = result2.get('object_id')
    print(f'object_id: {oid}')
    
    # Check DB persistence
    spaces = FounderSpace.query.all()
    print(f'Spaces in DB: {len(spaces)}')
    for s in spaces:
        print(f'  {s.space_id}: {s.name} ({s.space_type})')