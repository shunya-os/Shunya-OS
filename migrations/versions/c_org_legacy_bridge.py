"""C-stage — record the canonical legacy-tenant bridge for the Panchi Club org.

WHY
---
Production carries the founder's data split across two tenancy identities:

* legacy ``tenants`` row 89  — "Panchi Club", slug "panchi-club", from the
  pre-organizations schema. Legacy subsystems (documents, leads, campaigns,
  memory, observations, ...) wrote ``tenant_id = 89``.
* canonical ``organizations`` row 7 — "Panchi Club", slug "panchi-club".
  Canonical subsystems (relationships, suppliers) write ``organization_id = 7``.

Observed live on 2026-10-09 (cert/founder browser session): manual document
classification returned 404 for a document the same human could see in the
Documents workspace — the canonical reader filtered ``tenant_id == 7`` while
the row carried ``89``. ``organizations.legacy_tenant_id`` exists for exactly
this bridge and was NULL, so every call site had to guess.

WHAT
----
Guarded, evidence-asserted, no data rewrites:
  set ``organizations.legacy_tenant_id = 89`` for the organization whose
  name+slug both match the legacy tenant's name+slug, ONLY when the column is
  currently NULL and the legacy row exists. Any mismatch prints a truthful
  warning and skips (no guess). Downgrade clears the bridge (only when it
  still points at the asserted value).

The document/lead/... ROW convergence (rewriting tenant_id 89 -> 7 across 13
tables) is deliberately NOT done here: readers accept the bridge union
(resolve_tenant_scope), writers move toward canonical per subsystem, and the
full-table rewrite is a planned tenancy-convergence migration, not an
improvised one.

Revision ID: c_org_legacy_bridge
Revises: c_documents_content_sha256
"""
from sqlalchemy import text

revision = "c_org_legacy_bridge"
down_revision = "c_documents_content_sha256"
branch_labels = None
depends_on = None


def _bridge_candidate(bind):
    """The (org_id, legacy_id, ...) pair that both tables agree on, or None.

    Always returns ``(pair_or_none, rows)`` — the caller unpacks two values.
    """
    rows = bind.execute(text("""
        SELECT o.id, t.id, o.name, t.company_name, o.slug, t.slug
        FROM organizations o
        JOIN tenants t
          ON lower(o.name) = lower(t.company_name)
         AND lower(o.slug) = lower(t.slug)
        WHERE o.legacy_tenant_id IS NULL
        ORDER BY o.id
    """)).fetchall()
    if len(rows) == 1:
        return rows[0], rows
    return None, rows


def upgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    bind = op.get_bind()

    if not op.has_table("organizations") or not op.has_table("tenants"):
        print("  organizations/tenants absent — nothing to bridge")
        return

    if not op.has_column("organizations", "legacy_tenant_id"):
        print("  organizations.legacy_tenant_id absent — nothing to bridge")
        return

    pair, rows = _bridge_candidate(bind)
    if pair is None:
        print(f"  legacy bridge: expected exactly 1 name+slug match, "
              f"found {len(rows)} — skipping (no guess)")
        return

    org_id, legacy_id, oname, tname, oslug, tslug = pair
    print(f"  legacy bridge: organizations {org_id} ({oname}/{oslug}) "
          f"<-> tenants {legacy_id} ({tname}/{tslug})")

    bind.execute(text(
        "UPDATE organizations SET legacy_tenant_id = :t WHERE id = :o "
        "AND legacy_tenant_id IS NULL"),
        {"t": int(legacy_id), "o": int(org_id)})
    print(f"  organizations.legacy_tenant_id = {legacy_id} recorded for org {org_id}")


def downgrade():
    from migrations.guarded import guarded_op
    op = guarded_op()
    bind = op.get_bind()

    if not op.has_table("organizations"):
        return
    if not op.has_column("organizations", "legacy_tenant_id"):
        return

    pair, rows = _bridge_candidate(bind)
    # After upgrade the org no longer matches the NULL filter; find the
    # recorded bridge directly with the same name+slug assertion.
    rows2 = bind.execute(text("""
        SELECT o.id, o.legacy_tenant_id FROM organizations o
        JOIN tenants t
          ON lower(o.name) = lower(t.company_name)
         AND lower(o.slug) = lower(t.slug)
         AND t.id = o.legacy_tenant_id
        ORDER BY o.id
    """)).fetchall()
    if len(rows2) != 1:
        print(f"  legacy bridge downgrade: expected exactly 1 asserted pair, "
              f"found {len(rows2)} — skipping (no guess)")
        return
    org_id, legacy_id = rows2[0]
    bind.execute(text(
        "UPDATE organizations SET legacy_tenant_id = NULL WHERE id = :o "
        "AND legacy_tenant_id = :t"), {"o": int(org_id), "t": int(legacy_id)})
    print(f"  legacy bridge cleared for org {org_id}")