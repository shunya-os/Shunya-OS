"""
Genesis Verification Test — Phase 8
Verifies SHUNYA is in a pristine Genesis state.
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db

app = create_app()
print('App booted successfully')

with app.app_context():
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    print(f'\n=== Tables: {len(tables)} ===')

    # 1. Check no residual data
    print('\n--- Data Check ---')
    data_tables = []
    for t in tables:
        count = db.session.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
        if count > 0:
            data_tables.append((t, count))
    if not data_tables:
        print('  ALL TABLES: 0 ROWS — PRISTINE')
    else:
        for t, c in data_tables:
            print(f'  DATA FOUND: {t}: {c} rows')

    # 2. Check audit log table
    print('\n--- Audit Infrastructure ---')
    if 'genesis_audit_log' in tables:
        print('  genesis_audit_log: EXISTS')
        cols = [c['name'] for c in inspector.get_columns('genesis_audit_log')]
        print(f'  Columns: {cols}')
    else:
        print('  genesis_audit_log: MISSING')

    # 3. Check soft-delete columns
    print('\n--- Soft Delete Columns ---')
    sd_check = ['organizations', 'workspaces', 'founder_spaces', 'founder_objects', 'founder_relationships', 'org_members']
    for t in sd_check:
        if t in tables:
            cols = [c['name'] for c in inspector.get_columns(t)]
            has_sd = 'deleted_at' in cols
            has_restore = 'restored_at' in cols
            ok = 'OK' if has_sd else 'MISSING'
            print(f'  {ok}: {t} (deleted_at={has_sd}, restored_at={has_restore})')
        else:
            print(f'  SKIP: {t} not found')

    # 4. Check routes
    print('\n--- Protection Routes ---')
    routes_found = 0
    for rule in app.url_map.iter_rules():
        rule_str = str(rule.rule)
        if 'genesis' in rule_str:
            methods = sorted(set(rule.methods) - {'OPTIONS', 'HEAD'})
            print(f'  {rule_str} {" ".join(methods)}')
            routes_found += 1
    print(f'  Total: {routes_found} routes')

    # 5. Health check
    print('\n--- Health Check ---')
    with app.test_client() as client:
        resp = client.get('/health')
        print(f'  /health: {resp.status_code}')
        resp_data = resp.get_json()
        print(f'  database: {resp_data.get("database", "N/A")}')
        print(f'  status: {resp_data.get("status", "N/A")}')

        # Test audit endpoint
        resp = client.get('/api/v1/genesis/audit')
        print(f'  GET /api/v1/genesis/audit: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.get_json()
            print(f'  audit events: {len(data.get("data", []))}')

        # Test protection check
        resp = client.get('/api/v1/genesis/protect/check-identity/test-id')
        print(f'  GET /api/v1/genesis/protect/check-identity: {resp.status_code}')

        # Test landing page
        resp = client.get('/')
        print(f'  GET /: {resp.status_code}')

print('\n=== VERIFICATION COMPLETE ===')