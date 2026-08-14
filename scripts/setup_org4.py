"""Establish two genuinely separate organizations with distinct test users."""
import subprocess, json, sys, os

H = '/home/shunya-deploy/shunya_os'
PG = {'PGPASSWORD': 'Shunya@2026!', 'PATH': '/usr/bin:/bin', 'HOME': '/home/shunya-deploy'}

def q(sql):
    r = subprocess.run(['psql','-h','localhost','-U','shunya','-d','shunya_os','-t','-A','-c',sql],
        capture_output=True, text=True, timeout=15, env=PG)
    return r.stdout.strip()

print("=== CURRENT ORG STATE ===")
print("Organizations:", q("SELECT id, name, legacy_tenant_id FROM organizations"))
sql_org1 = "SELECT id, identity_id, role FROM org_members WHERE organization_id=1 AND is_active=true LIMIT 5"
sql_org4 = "SELECT id, identity_id, role FROM org_members WHERE organization_id=4 AND is_active=true"
print("Org 1 members:", q(sql_org1))
print("Org 4 members:", q(sql_org4))
print("OrgMember total:", q("SELECT count(*) FROM org_members"))
print("TeamMembers:", q("SELECT count(*) FROM team_members"))

# Create org 4 test user (distinct from org 1 users)
# tenant-b@verify.com was created earlier and assigned to org 1 (Panchi Club)
# We need a user genuinely in org 4 (Demo SHUNYA)
print("\n=== CREATING ORG 4 TEST USER ===")

# Use the app to create a TeamMember + OrgMember in org 4 with member role
script = '''
import sys, os
sys.path.insert(0, "/home/shunya-deploy/shunya_os")
os.chdir("/home/shunya-deploy/shunya_os")
from app import create_app, db
from app.auth import TeamMember
from app.models import OrgMember, Organization
from app.authz.models import Role, OrgMemberRole

app = create_app()
with app.app_context():
    email = "org4-admin@shunyaos.com"
    name = "Org 4 Admin"
    
    tm = TeamMember.query.filter_by(email=email).first()
    if not tm:
        tm = TeamMember(name=name, email=email, role="admin", is_active=True)
        tm.set_password("Test1234!")
        db.session.add(tm)
        db.session.flush()
        print("TeamMember created:", tm.id)
    else:
        print("TeamMember exists:", tm.id)
    
    org = Organization.query.filter_by(id=4).first()
    if not org:
        print("Org 4 not found!")
        sys.exit(1)
    
    om = OrgMember.query.filter_by(organization_id=4, identity_id=email).first()
    if not om:
        om = OrgMember(organization_id=4, identity_id=email, name=name, email=email, role="admin", is_active=True)
        db.session.add(om)
        db.session.flush()
        print("OrgMember created:", om.id)
    else:
        print("OrgMember exists:", om.id)
    
    # Assign admin role
    role = Role.query.filter_by(organization_id=4, name="admin").first()
    if not role:
        # Seed roles for org 4
        from app.authz.services import seed_default_roles
        seed_default_roles(4)
        role = Role.query.filter_by(organization_id=4, name="admin").first()
    if role:
        existing = OrgMemberRole.query.filter_by(organization_id=4, member_id=om.id, role_id=role.id).first()
        if not existing:
            db.session.add(OrgMemberRole(organization_id=4, member_id=om.id, role_id=role.id, granted_by="system"))
            print("Role assigned: admin")
    
    db.session.commit()
    print("ORG 4 SETUP COMPLETE")
'''

r = subprocess.run(['.venv/bin/python3', '-c', script], capture_output=True, text=True, timeout=60, cwd=H,
    env={'PYTHONPATH': H, 'PATH': f'{H}/.venv/bin:/usr/bin:/bin', 'HOME': '/home/shunya-deploy'})
print(r.stdout)
if r.stderr:
    errs = [l for l in r.stderr.split('\n') if 'Error' in l or 'Traceback' in l]
    if errs: print("STDERR:", errs[:3])

# Verify
print("\n=== VERIFY ORG 4 ===")
print("Org 4 members:", q(sql_org4))
print("Org 4 roles:", q("SELECT r.name FROM auth_roles r WHERE r.organization_id=4"))
print("Org 4 role assignments:", q("SELECT count(*) FROM auth_member_roles WHERE organization_id=4"))