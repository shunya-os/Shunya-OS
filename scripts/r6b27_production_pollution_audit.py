#!/usr/bin/env python3
"""R6B-2.7 §8 — READ-ONLY quantification of production test pollution.

Strictly SELECT-only. Does NOT import create_app() (which writes:
db.create_all() + _seed_default_workspaces()). Uses a bare engine so this
audit can never mutate production.

Reports:
  - sh_objects totals and object_type distribution
  - object_type='test' rows: count, org, workspace, creation window, samples
  - sh_workspaces rows (incl. spc_default / NULL organization_id)
  - sh_objects referencing workspace_id='spc_default'
  - organizations referenced by the test rows
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import create_engine, text

URL = os.environ.get("DATABASE_URL", "")
if not URL:
    print("NO DATABASE_URL — aborting")
    raise SystemExit(2)

engine = create_engine(URL)

SAFE_PREFIXES = ("select", "with")


def q(conn, sql, **params):
    assert sql.strip().lower().startswith(SAFE_PREFIXES), f"non-read-only: {sql[:40]}"
    return conn.execute(text(sql), params).fetchall()


def main() -> int:
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        print("== engine:", URL.split("@")[-1] if "@" in URL else URL)

        total = q(conn, "select count(*) from sh_objects")[0][0]
        print(f"\n[1] sh_objects total: {total}")

        print("\n[2] sh_objects by object_type:")
        for row in q(conn, """
            select object_type, count(*) c
            from sh_objects group by object_type order by c desc
        """):
            print(f"    {row[0]!r:30} {row[1]}")

        print("\n[3] object_type='test' by organization_id:")
        rows = q(conn, """
            select organization_id, count(*) c
            from sh_objects where object_type='test'
            group by organization_id order by c desc
        """)
        for row in rows:
            print(f"    org={row[0]!r:8} count={row[1]}")

        print("\n[4] object_type='test' by workspace_id:")
        for row in q(conn, """
            select workspace_id, count(*) c
            from sh_objects where object_type='test'
            group by workspace_id order by c desc limit 20
        """):
            print(f"    ws={row[0]!r:30} count={row[1]}")

        print("\n[5] object_type='test' creation window:")
        row = q(conn, """
            select min(created_at), max(created_at), count(distinct created_at::date) d
            from sh_objects where object_type='test'
        """)[0]
        print(f"    min={row[0]}  max={row[1]}  distinct_days={row[2]}")

        print("\n[6] object_type='test' by created_at date:")
        for row in q(conn, """
            select created_at::date d, count(*) c
            from sh_objects where object_type='test'
            group by d order by d
        """):
            print(f"    {row[0]}  {row[1]}")

        print("\n[7] sample object_type='test' rows (id, name, org, ws, created_at):")
        for row in q(conn, """
            select id, name, organization_id, workspace_id, created_at
            from sh_objects where object_type='test'
            order by created_at limit 8
        """):
            print(f"    {row[0]} | {row[1]!r} | org={row[2]} | ws={row[3]!r} | {row[4]}")
        print("    ... (most recent 8)")
        for row in q(conn, """
            select id, name, organization_id, workspace_id, created_at
            from sh_objects where object_type='test'
            order by created_at desc limit 8
        """):
            print(f"    {row[0]} | {row[1]!r} | org={row[2]} | ws={row[3]!r} | {row[4]}")

        print("\n[8] sh_workspaces (all rows):")
        for row in q(conn, """
            select id, name, workspace_type, organization_id, created_by, created_at
            from sh_workspaces order by id
        """):
            print(f"    id={row[0]!r:16} name={row[1]!r:14} type={row[2]!r:10} org={row[3]!r:6} by={row[4]!r} {row[5]}")

        print("\n[9] sh_workspaces with NULL organization_id:")
        for row in q(conn, "select id, name, organization_id from sh_workspaces where organization_id is null"):
            print(f"    {row[0]!r} ({row[1]!r})")

        print("\n[10] sh_objects referencing workspace_id='spc_default':")
        rows = q(conn, """
            select id, object_id, object_type, name, organization_id, status, is_deleted, created_at
            from sh_objects where workspace_id='spc_default' order by id
        """)
        print("     count =", len(rows))
        for row in rows:
            print(f"     id={row[0]} object_id={row[1]} type={row[2]!r} name={row[3]!r} "
                  f"org={row[4]} status={row[5]!r} deleted={row[6]} created={row[7]}")

        print("\n[10b] sh_workspaces status for spc_default:")
        for row in q(conn, "select id, status, created_at, updated_at from sh_workspaces where id='spc_default'"):
            print(f"     id={row[0]!r} status={row[1]!r} created_at={row[2]} updated_at={row[3]}")

        print("\n[10c] other relations referencing the literal 'spc_default':")
        print("     sh_objects.workspace_id =",
              q(conn, "select count(*) from sh_objects where workspace_id='spc_default'")[0][0])
        for tbl in ("user_workspaces", "workspace_memberships", "user_workspace_memberships"):
            exists = q(conn, "select to_regclass(:t) is not null", t=tbl)[0][0]
            if not exists:
                print(f"     {tbl} = (table absent)")
                continue
            try:
                print(f"     {tbl} =", q(conn, f"select count(*) from {tbl} where workspace_id='spc_default'")[0][0])
            except Exception as exc:
                conn.rollback()
                print(f"     {tbl} = (not queryable: {type(exc).__name__})")

        print("\n[11] organizations referenced by test rows:")
        for row in q(conn, """
            select o.id, o.name, count(*) c
            from sh_objects s left join organizations o on o.id = s.organization_id
            where s.object_type='test'
            group by o.id, o.name order by c desc limit 10
        """):
            print(f"    org={row[0]!r} name={row[1]!r} count={row[2]}")

        print("\n[12] sh_workspace_memberships count:")
        print("     ", q(conn, "select count(*) from sh_workspace_memberships")[0][0])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
