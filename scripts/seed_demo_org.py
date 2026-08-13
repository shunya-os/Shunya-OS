"""Seed OrgMember + Workspace for demo account via the app's real DB connection."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# Load the real .env
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, '.env'))

from app import create_app, db
app = create_app()
with app.app_context():
    from app.models import Organization, OrgMember
    from app.auth import TeamMember
    from app.production.identity.workspace_model import Workspace
    print('DB URI:', app.config.get('SQLALCHEMY_DATABASE_URI', '')[:60])
    tm = TeamMember.query.filter_by(email='demo@shunyaos.com').first()
    if not tm:
        print('ERROR: Demo TeamMember not found')
        exit(1)
    print('TeamMember:', tm.id, tm.email, tm.role)
    org = Organization.query.filter_by(slug='shunya-demo').first()
    if not org:
        org = Organization(name='SHUNYA Demo', slug='shunya-demo')
        db.session.add(org); db.session.flush()
        print('Created org', org.id)
    om = OrgMember.query.filter_by(email='demo@shunyaos.com').first()
    if not om:
        om = OrgMember(organization_id=org.id, identity_id=f'u{tm.id}', email='demo@shunyaos.com', role='owner', is_active=True)
        db.session.add(om); db.session.flush()
        print('Created OrgMember', om.identity_id)
    ws = Workspace.query.filter_by(organization_id=org.id).first()
    if not ws:
        ws = Workspace(organization_id=org.id, name='Demo Workspace', slug='demo-workspace', created_by='demo@shunyaos.com')
        db.session.add(ws)
        print('Created Workspace')
    db.session.commit()
    print(f'OK: org={org.id} om={om.identity_id} ws={ws.id if ws else None}')