"""Check tenant relationships."""
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check organizations tenant mapping
    rows = db.session.execute(text("""
        SELECT o.id, o.name, o.legacy_tenant_id, t.id as tenant_id, t.company_name
        FROM organizations o
        LEFT JOIN tenants t ON o.legacy_tenant_id = t.id
        ORDER BY o.id
    """)).fetchall()
    print("=== Organizations -> Tenants ===")
    for r in rows:
        print(f"  org#{r.id} '{r.name}': legacy_tenant_id={r.legacy_tenant_id}, tenant#{r.tenant_id} '{r.company_name or '?'}'")
    
    # Check team_members with their tenants
    rows = db.session.execute(text("""
        SELECT tm.id, tm.email, tm.tenant_id, t.company_name
        FROM team_members tm
        LEFT JOIN tenants t ON tm.tenant_id = t.id
        ORDER BY tm.id
    """)).fetchall()
    print("=== Team Members -> Tenants ===")
    for r in rows:
        print(f"  tm#{r.id} '{r.email}': tenant_id={r.tenant_id}, tenant='{r.company_name or '?'}'")
    
    # Check tenants
    rows = db.session.execute(text("SELECT id, company_name, is_active FROM tenants ORDER BY id")).fetchall()
    print("=== Tenants ===")
    for r in rows:
        print(f"  tenant#{r.id} '{r.company_name}': active={r.is_active}")
    
    # Check organizations without tenant link
    rows = db.session.execute(text("""
        SELECT o.id, o.name
        FROM organizations o
        WHERE o.legacy_tenant_id IS NULL
    """)).fetchall()
    print("=== Organizations without legacy_tenant_id ===")
    for r in rows:
        print(f"  org#{r.id} '{r.name}'")