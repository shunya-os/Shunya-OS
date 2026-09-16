"""R6B-2.7 Window 1 — READ-ONLY production ownership reconciliation.

Connects using the application's own DATABASE_URL (loaded from .env). The
credential is never printed. The session is opened READ ONLY and
default_transaction_read_only is forced, so no write is possible.

Emits an inventory of organizations, memberships, workspaces and the
candidate workspace mappings for human classification.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path("/home/shunya-deploy/shunya_os")
OUT = REPO / "artifacts" / "r6b25" / "r6b27_production_inventory.json"


def load_url() -> str:
    from dotenv import dotenv_values
    env = dotenv_values(REPO / ".env")
    url = env.get("DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("no DATABASE_URL available")
    return url


QUERIES = {
    "organizations_total": "SELECT count(*) FROM organizations",
    "identities_with_membership": (
        "SELECT count(DISTINCT identity_id) FROM org_members WHERE is_active = true"),
    "identities_multi_org": (
        "SELECT count(*) FROM (SELECT identity_id FROM org_members "
        "WHERE is_active = true GROUP BY identity_id HAVING count(DISTINCT organization_id) > 1) t"),
    "org_members_total": "SELECT count(*) FROM org_members",
    "org_members_active": "SELECT count(*) FROM org_members WHERE is_active = true",
    "sh_workspaces_total": "SELECT count(*) FROM sh_workspaces",
    "sh_workspaces_null_org": "SELECT count(*) FROM sh_workspaces WHERE organization_id IS NULL",
    "sh_workspaces_active": "SELECT count(*) FROM sh_workspaces WHERE status = 'active'",
    "sh_workspaces_with_objects": (
        "SELECT count(DISTINCT w.id) FROM sh_workspaces w "
        "JOIN sh_objects o ON o.workspace_id = w.id"),
    "sh_objects_total": "SELECT count(*) FROM sh_objects",
    "user_workspaces_total": "SELECT count(*) FROM user_workspaces",
    "user_workspaces_null_org": "SELECT count(*) FROM user_workspaces WHERE organization_id IS NULL",
    "uwm_total": "SELECT count(*) FROM user_workspace_memberships",
    "uwm_active": "SELECT count(*) FROM user_workspace_memberships WHERE is_active = true",
    "third_workspaces_total": (
        "SELECT count(*) FROM pg_class WHERE relname = 'workspaces' AND relkind = 'r'"),
    "founder_spaces_total": "SELECT count(*) FROM founder_spaces",
    "founder_objects_total": "SELECT count(*) FROM founder_objects",
}

LISTS = {
    "sh_workspaces": (
        "SELECT id, organization_id, status, created_by, workspace_type "
        "FROM sh_workspaces ORDER BY organization_id NULLS FIRST, id"),
    "user_workspaces": (
        "SELECT workspace_id, owner_identity_id, organization_id, status "
        "FROM user_workspaces ORDER BY id"),
    "uwm_sample": (
        "SELECT identity_id, workspace_id, role, is_active "
        "FROM user_workspace_memberships ORDER BY workspace_id LIMIT 40"),
    "multi_org_identities": (
        "SELECT identity_id, count(DISTINCT organization_id) AS orgs "
        "FROM org_members WHERE is_active = true GROUP BY identity_id "
        "HAVING count(DISTINCT organization_id) > 1 ORDER BY orgs DESC LIMIT 40"),
    "sh_workspaces_ranked_per_org": (
        "SELECT organization_id, count(*) AS ws_count FROM sh_workspaces "
        "WHERE organization_id IS NOT NULL GROUP BY organization_id "
        "HAVING count(*) > 1 ORDER BY ws_count DESC LIMIT 20"),
    "orphan_uwm": (
        "SELECT m.identity_id, m.workspace_id FROM user_workspace_memberships m "
        "LEFT JOIN user_workspaces w ON w.id = m.workspace_id WHERE w.id IS NULL LIMIT 20"),
    "uw_org_null_with_objects_hint": (
        "SELECT w.workspace_id, w.owner_identity_id FROM user_workspaces w "
        "WHERE w.organization_id IS NULL LIMIT 20"),
}


def main() -> int:
    import psycopg2
    url = load_url()
    safe = url.split("@")[-1]
    print(f"connecting (read-only) to host/db portion: ...@{safe}")

    conn = psycopg2.connect(url)
    conn.set_session(readonly=True, autocommit=False)
    result = {"host_db": safe, "counts": {}, "lists": {}}
    with conn.cursor() as cur:
        cur.execute("SHOW default_transaction_read_only")
        result["default_transaction_read_only"] = cur.fetchone()[0]
        cur.execute("SELECT current_setting('transaction_read_only')")
        result["transaction_read_only"] = cur.fetchone()[0]
        cur.execute("SHOW server_version")
        result["server_version"] = cur.fetchone()[0]

        for name, sql in QUERIES.items():
            try:
                cur.execute(sql)
                result["counts"][name] = cur.fetchone()[0]
            except Exception as exc:
                conn.rollback()
                result["counts"][name] = f"ERROR: {exc.__class__.__name__}"

        for name, sql in LISTS.items():
            try:
                cur.execute(sql)
                cols = [d[0] for d in cur.description]
                result["lists"][name] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as exc:
                conn.rollback()
                result["lists"][name] = f"ERROR: {exc}"

    conn.rollback()
    conn.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result["counts"], indent=2))
    for name, rows in result["lists"].items():
        if isinstance(rows, str):
            print(f"{name}: {rows}")
        else:
            print(f"{name}: {len(rows)} rows")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
