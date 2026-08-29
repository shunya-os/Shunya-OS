"""Check DB schema for tenant isolation."""
from app import create_app, db
app = create_app()
with app.app_context():
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)

    # Check organization-related tables
    tables = inspector.get_table_names()
    org_tables = [t for t in tables if 'org' in t.lower() or 'member' in t.lower()]
    print('=== Organization-related tables ===')
    for t in sorted(org_tables):
        cols = inspector.get_columns(t)
        print('  %s:' % t)
        for c in cols:
            print('    %s: type=%s, nullable=%s' % (c["name"], c["type"], c.get("nullable")))
        print()

    # Show existing tenants
    print('=== Tenants ===')
    rows = db.session.execute(text('SELECT id, company_name, slug FROM tenants ORDER BY id')).fetchall()
    if rows:
        for r in rows:
            print('  id=%d, name=%s, slug=%s' % (r[0], r[1], r[2]))
    else:
        print('  (no tenants yet)')

    # Show team_members
    print()
    print('=== TeamMembers ===')
    rows = db.session.execute(text('SELECT id, name, email, tenant_id, role FROM team_members ORDER BY id')).fetchall()
    if rows:
        for r in rows:
            print('  id=%d, name=%s, email=%s, tenant_id=%s, role=%s' % (r[0], r[1], r[2], r[3], r[4]))
    else:
        print('  (no team members)')

    # Show documents
    print()
    print('=== Documents (first 5) ===')
    rows = db.session.execute(text('SELECT id, lead_id, filename, tenant_id FROM documents ORDER BY id LIMIT 5')).fetchall()
    if rows:
        for r in rows:
            print('  id=%d, lead_id=%s, filename=%s, tenant_id=%s' % (r[0], r[1], r[2], r[3]))
    else:
        print('  (no documents)')

    # Show leads
    print()
    print('=== Leads ===')
    rows = db.session.execute(text('SELECT id, code, customer_name, tenant_id FROM leads ORDER BY id')).fetchall()
    if rows:
        for r in rows:
            print('  id=%d, code=%s, customer=%s, tenant_id=%s' % (r[0], r[1], r[2], r[3]))

    # Show all other tables with tenant_id
    print()
    print('=== Other tables with tenant_id ===')
    for t in sorted(tables):
        cols = [c for c in inspector.get_columns(t) if 'tenant' in c['name'].lower()]
        if cols and t not in ('leads', 'documents', 'team_members', 'task_lists', 'notifications'):
            print('  %s' % t)
            for c in cols:
                print('    %s: type=%s, nullable=%s' % (c["name"], c["type"], c.get("nullable")))