#!/usr/bin/env python3
"""Debug space creation on PostgreSQL.

Requires DATABASE_URL to be set in the environment. Exits with an
error message before importing the application if it is missing or
empty, preventing accidental connection to a real database.
"""
import os
import sys

_DB_URL = os.environ.get("DATABASE_URL", "")
if not _DB_URL:
    sys.exit(
        "ERROR: DATABASE_URL is not set.\n\n"
        "This script requires an explicit database URL. Set it before running:\n\n"
        "  DATABASE_URL=postgresql://user:***@host:port/dbname  \\\n"
        "  python3 scripts/debug_space_creation.py\n"
    )

os.environ['SECRET_KEY'] = 'test-secret'
os.environ['DISABLE_RATE_LIMIT'] = 'true'
os.environ['WTF_CSRF_ENABLED'] = 'False'

from app import create_app, db
from app.founder.models import FounderSpace, FounderObject

app = create_app(config_override={
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': _DB_URL,
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