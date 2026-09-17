#!/usr/bin/env python3
"""PRODUCTION journey proof — Content Studio lifecycle on the DEPLOYED build.

Runs the real HTTP routes through the production application object (same
process configuration, same PostgreSQL database the live service uses) and
walks the complete state machine, including permanent delete.

Self-cleaning: operates on rows it creates itself and removes them at the end,
so no lasting production data is added or altered.

Usage:  .venv/bin/python scripts/verify_content_lifecycle_journey_prod.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OWNER = "sid_a3cd655b1e6f4b0f9c1113ba7ec26d41"  # existing content owner
THIEF = "sid_89f7489ab87b47fb9d0ad129ebbb467b"  # unrelated identity

RESULTS = []


def check(name, ok, detail=None):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' — ' + str(detail)) if detail else ''}")


def main() -> int:
    os.environ.setdefault("SHUNYA_ENVIRONMENT", "production")
    from app import create_app, db
    from app.integration.models import ContentGeneration

    app = create_app()
    created = []

    with app.app_context():
        def mk(tag, identity=OWNER):
            cg = ContentGeneration(
                identity_id=identity, content_type="blog_post",
                prompt=f"CERTIFICATION {tag}", generated_content="x",
                status="active", is_deleted=False,
            )
            db.session.add(cg)
            db.session.commit()
            created.append(cg.id)
            return cg.id

        def state(iid):
            r = db.session.get(ContentGeneration, iid)
            if r is None:
                return None
            if r.is_deleted:
                return "trashed"
            return "archived" if r.status == "archived" else "active"

        # ── ACTIVE → ARCHIVED → ACTIVE ────────────────────────────────
        iid = mk("archive-restore")
        with app.test_client() as c:
            with c.session_transaction() as s:
                s["identity_id"] = OWNER
                s["current_org_id"] = 1
            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "archive"})
            check("archive: HTTP 200", r.status_code == 200, r.get_json())
            check("archive: DB state", state(iid) == "archived", state(iid))

            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "restore"})
            check("restore: HTTP 200", r.status_code == 200, r.get_json())
            check("restore: DB state", state(iid) == "active", state(iid))

            # ── ACTIVE → TRASHED → ACTIVE ─────────────────────────────
            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "trash"})
            check("trash: HTTP 200", r.status_code == 200, r.get_json())
            check("trash: DB state", state(iid) == "trashed", state(iid))
            # Trashed items must remain listable — the library is a single
            # state-aware surface, and Recover / Permanent Delete are only
            # reachable from a trashed row. Excluding them here would make the
            # lifecycle unreachable.
            h = c.get("/api/v1/content/history").get_json()
            check("history: HTTP success flag",
                  h.get("success") is True, h.get("total"))
            row = next((i for i in h.get("data", []) if i["id"] == iid), None)
            check("trash: row still listed and reports trashed state",
                  row is not None and row["is_deleted"] is True,
                  f"total={h.get('total')} row={row}")

            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "recover"})
            check("recover: HTTP 200", r.status_code == 200, r.get_json())
            check("recover: DB state", state(iid) == "active", state(iid))

            # ── Invalid transitions ───────────────────────────────────
            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "archive"})
            c.post(f"/api/v1/content/history/{iid}/lifecycle",
                   json={"action": "archive"})
            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "archive"})
            check("invalid transition → 409 (not 400/fake success)",
                  r.status_code == 409, r.get_json().get("error"))

            # ── Permanent delete requires trash ───────────────────────
            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "permanent_delete"})
            check("permanent_delete blocked while ARCHIVED",
                  r.status_code == 409, r.get_json().get("error"))

            # ── Authorization: another identity ───────────────────────
            with app.test_client() as c2:
                with c2.session_transaction() as s:
                    s["identity_id"] = THIEF
                    s["current_org_id"] = 1
                r = c2.post(f"/api/v1/content/history/{iid}/lifecycle",
                            json={"action": "permanent_delete"})
                check("cross-identity delete → 404 (no existence leak)",
                      r.status_code == 404, r.get_json())
                check("cross-identity did not delete",
                      state(iid) is not None, state(iid))

            # ── Permanent delete from trash ───────────────────────────
            c.post(f"/api/v1/content/history/{iid}/lifecycle",
                   json={"action": "restore"})
            c.post(f"/api/v1/content/history/{iid}/lifecycle",
                   json={"action": "trash"})
            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "permanent_delete"})
            check("permanent_delete: HTTP 200", r.status_code == 200,
                  r.get_json())
            check("permanent_delete: row removed", state(iid) is None)
            created.remove(iid)

            r = c.post(f"/api/v1/content/history/{iid}/lifecycle",
                       json={"action": "permanent_delete"})
            check("repeat permanent_delete → truthful 404",
                  r.status_code == 404, r.get_json())

            # ── Unauthenticated ───────────────────────────────────────
            with app.test_client() as c3:
                r = c3.post(f"/api/v1/content/history/{iid}/lifecycle",
                            json={"action": "archive"})
                check("unauthenticated → 401", r.status_code == 401)

        # Clean up anything left behind by an early failure.
        for i in list(created):
            row = db.session.get(ContentGeneration, i)
            if row is not None:
                db.session.delete(row)
        db.session.commit()

    failures = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failures)}/{len(RESULTS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
