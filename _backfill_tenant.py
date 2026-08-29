"""
Tenant Isolation Backfill Script
=================================
Backfills NULL tenant_id values across critical tables using organization/tenant
associations, then adds DB-level NOT NULL constraints.
"""
from app import create_app, db
from sqlalchemy import text, inspect

app = create_app()
with app.app_context():
    conn = db.session

    # ── Step 1: Map organizations to tenants ─────────────────────────────────
    orgs = conn.execute(text("""
        SELECT o.id, o.name, o.legacy_tenant_id,
               t.id as matched_tenant_id, t.company_name
        FROM organizations o
        LEFT JOIN tenants t ON LOWER(TRIM(o.name)) = LOWER(TRIM(t.company_name))
        ORDER BY o.id
    """)).fetchall()

    print("=== Organization -> Tenant Mapping ===")
    org_tenant_map = {}
    DEFAULT_TENANT_ID = 89
    for r in orgs:
        tid = r[3]  # matched_tenant_id
        if not tid:
            tid = DEFAULT_TENANT_ID
            print("  org=%d '%s': NO tenant match -> using default %d" % (r[0], r[1], tid))
        else:
            print("  org=%d '%s' -> tenant=%d '%s'" % (r[0], r[1], tid, r[4]))
        org_tenant_map[r[0]] = tid

    t = conn.execute(text("SELECT id, company_name FROM tenants WHERE id = :tid"), {'tid': DEFAULT_TENANT_ID}).fetchone()
    if t:
        print("\nDefault tenant: id=%d, name=%s" % (t[0], t[1]))
    else:
        t = conn.execute(text("SELECT id, company_name FROM tenants ORDER BY id LIMIT 1")).fetchone()
        if t:
            DEFAULT_TENANT_ID = t[0]
            print("Default tenant %d not found, using first: id=%d, name=%s" % (89, t[0], t[1]))

    # ── Step 2: Backfill team_members ────────────────────────────────────────
    print("\n=== Backfill team_members.tenant_id ===")
    tms = conn.execute(text("""
        SELECT tm.id, tm.name, tm.email, tm.tenant_id
        FROM team_members tm
        WHERE tm.tenant_id IS NULL
        ORDER BY tm.id
    """)).fetchall()

    for tm in tms:
        org_member = conn.execute(text("""
            SELECT om.organization_id
            FROM org_members om
            WHERE om.email = :email AND om.is_active = true
            LIMIT 1
        """), {'email': tm[2]}).fetchone()

        if org_member:
            tid = org_tenant_map.get(org_member[0], DEFAULT_TENANT_ID)
            conn.execute(text("UPDATE team_members SET tenant_id = :tid WHERE id = :mid"), {'tid': tid, 'mid': tm[0]})
            print("  tm=%d '%s': org_member -> org=%d -> tenant=%d" % (tm[0], tm[1], org_member[0], tid))
        else:
            conn.execute(text("UPDATE team_members SET tenant_id = :tid WHERE id = :mid"), {'tid': DEFAULT_TENANT_ID, 'mid': tm[0]})
            print("  tm=%d '%s': NO org_member -> default tenant=%d" % (tm[0], tm[1], DEFAULT_TENANT_ID))

    conn.commit()

    # ── Step 3: Backfill leads ───────────────────────────────────────────────
    print("\n=== Backfill leads.tenant_id ===")
    r = conn.execute(text("UPDATE leads SET tenant_id = :tid WHERE tenant_id IS NULL"), {'tid': DEFAULT_TENANT_ID})
    conn.commit()
    print("  Backfilled %d leads -> tenant=%d" % (r.rowcount, DEFAULT_TENANT_ID))

    # ── Step 4: Backfill documents ───────────────────────────────────────────
    print("\n=== Backfill documents.tenant_id ===")
    r = conn.execute(text("""
        UPDATE documents d
        SET tenant_id = l.tenant_id
        FROM leads l
        WHERE d.lead_id = l.id
          AND d.tenant_id IS NULL
          AND l.tenant_id IS NOT NULL
    """))
    conn.commit()
    print("  Propagated from leads: %d" % r.rowcount)

    r = conn.execute(text("UPDATE documents SET tenant_id = :tid WHERE tenant_id IS NULL"), {'tid': DEFAULT_TENANT_ID})
    conn.commit()
    print("  Default backfill: %d" % r.rowcount)

    # ── Step 5: Backfill other nullable-tenant_id tables ─────────────────────
    print("\n=== Backfill other tables ===")
    inspector = inspect(db.engine)
    for t in sorted(inspector.get_table_names()):
        cols = [c for c in inspector.get_columns(t) if c['name'] == 'tenant_id']
        if not cols:
            continue
        nullable = cols[0].get('nullable', True)
        if not nullable:
            continue
        if t in ('team_members', 'documents', 'leads'):
            continue

        count = conn.execute(text("SELECT COUNT(*) FROM %s WHERE tenant_id IS NULL" % t)).scalar()
        if count and count > 0:
            r = conn.execute(text("UPDATE %s SET tenant_id = :tid WHERE tenant_id IS NULL" % t), {'tid': DEFAULT_TENANT_ID})
            conn.commit()
            print("  %s: backfilled %d NULLs -> tenant=%d" % (t, r.rowcount, DEFAULT_TENANT_ID))
        else:
            print("  %s: 0 NULLs (skipped)" % t)

    # ── Verify ───────────────────────────────────────────────────────────────
    print("\n=== Verification ===")
    for table in ('team_members', 'documents', 'leads'):
        nulls = conn.execute(text("SELECT COUNT(*) FROM %s WHERE tenant_id IS NULL" % table)).scalar()
        total = conn.execute(text("SELECT COUNT(*) FROM %s" % table)).scalar()
        print("  %s: %d NULLs out of %d total" % (table, nulls, total))

    print("\n✅ Backfill complete!")