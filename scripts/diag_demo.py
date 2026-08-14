"""Diagnose which DB the running app uses + demo signin path."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, '.env'), override=False)
print('ENV FLASK_ENV:', os.getenv('FLASK_ENV'))
print('ENV DATABASE_URL len:', len(os.getenv('DATABASE_URL', '')))
from app import create_app, db
app = create_app()
uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
print('App DB URI (first 40):', uri[:40])
with app.app_context():
    from app.models import OrgMember, Organization
    from app.auth import TeamMember
    print('All orgs:', [(o.id, o.slug) for o in Organization.query.all()])
    print('All OrgMembers:', [(om.id, om.email, om.organization_id, om.identity_id) for om in OrgMember.query.all()])
    print('TeamMembers:', [(t.id, t.email) for t in TeamMember.query.all()])