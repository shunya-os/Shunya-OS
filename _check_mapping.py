"""Check org_members and organizations mapping for backfill plan."""
from app import create_app, db
app = create_app()
with app.app_context():
    from sqlalchemy import text
    
    # Check organizations
    print('=== Organizations ===')
    rows = db.session.execute(text('SELECT id, name, slug, legacy_tenant_id FROM organizations ORDER BY id')).fetchall()
    for r in rows:
        print('  id=%d, name=%s, slug=%s, legacy_tenant_id=%s' % (r[0], r[1], r[2], r[3]))
    
    # Check org_members
    print()
    print('=== OrgMembers ===')
    rows = db.session.execute(text('SELECT id, organization_id, identity_id, email, role FROM org_members ORDER BY id')).fetchall()
    for r in rows:
        print('  id=%d, org_id=%d, identity_id=%s, email=%s, role=%s' % (r[0], r[1], r[2], r[3], r[4]))
    
    # Check how identity_id relates to team_members
    print()
    print('=== TeamMembers emails and org_members matching ===')
    tms = db.session.execute(text('SELECT id, name, email FROM team_members ORDER BY id')).fetchall()
    for tm in tms:
        oms = db.session.execute(text('SELECT organization_id, identity_id FROM org_members WHERE email = :e'), {'e': tm[2]}).fetchall()
        if oms:
            for om in oms:
                org = db.session.execute(text('SELECT name, legacy_tenant_id FROM organizations WHERE id = :oid'), {'oid': om[0]}).fetchone()
                print('  tm=%d (%s): org_id=%d (%s), identity_id=%s, legacy_tenant_id=%s' % (tm[0], tm[2], om[0], org[0] if org else '?', om[1], org[1] if org else '?'))
        else:
            print('  tm=%d (%s): NO org_member found' % (tm[0], tm[2]))