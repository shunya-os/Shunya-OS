#!/usr/bin/env python3
"""M6 runtime proof — semantic customer/supplier ingestion on the DEPLOYED build.

Walks the complete M6 contract over real HTTPS against production, in the
isolated certification tenant (org 278):

  INSPECT → UNDERSTAND → MAP (explained) → DETECT AMBIGUITY → PREVIEW
  → HUMAN CONFIRMATION → CANONICAL PERSISTENCE → PROVENANCE → CORRECTION
  → DUPLICATE RESOLUTION → FAILURE + RECOVERY → ISOLATION

The certification login is read from the 0600 credential file; values are
never printed. Prints PASS/FAIL lines; exits non-zero on any failure.

Usage:
    .venv/bin/python scripts/verify_m6_ingestion_runtime.py
"""
import os
import sys
import time

sys.path.insert(0, "/home/shunya-deploy/shunya_os")
sys.path.insert(0, "/home/shunya-deploy/shunya_os/scripts")

os.environ.setdefault("SHUNYA_ENVIRONMENT", "production")

from verify_continue07_runtime import Http, read_login, BASE, WORKSPACE_ID  # noqa: E402

CERT_ORG = 278
CERT_IDENTITY = "sid_5ef358418d4246ba8e156de0"

RESULTS = []


def check(name, ok, detail=None):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}"
          + (f" — {detail}" if detail is not None else ""))


def finish() -> int:
    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED: " + "; ".join(failed))
    return 1 if failed else 0


def main() -> int:
    stamp = int(time.time())
    suffix = str(stamp)[-6:]

    cert = Http(BASE)
    email, password = read_login()
    status, _h, raw = cert.call("POST", "/api/v1/founder/signin",
                                payload={"email": email, "password": password,
                                         "org_id": CERT_ORG})
    ok = status == 200 and b'"success": true' in raw.replace(b'"success":true', b'"success": true')
    check("0 certification sign-in over HTTPS", ok, f"status={status}")
    if not ok:
        return finish()

    # ═══════════════════════════════════════════════════════════════════
    # CUSTOMER INGESTION
    # ═══════════════════════════════════════════════════════════════════
    cust_name_a = f"M6 Cert Meera {suffix}"
    cust_name_b = f"M6 Cert Arjun {suffix}"
    # Phones must be run-unique too: customer matching is by email OR phone,
    # so fixed numbers match the previous run's records and turn every row
    # into a (correct) duplicate skip — created=0, failing C6 for the wrong
    # reason. Derive both phones from the full timestamp.
    phone_a = f"+91 9{str(stamp)[-9:]}"
    phone_b = f"+91 8{str(stamp)[-9:]}"
    cust_csv = (
        "Client Name,Mobile,Email,Company,City\n"
        f"{cust_name_a},{phone_a},m6a{suffix}@example.com,Saffron Travels,Delhi\n"
        f"{cust_name_b},{phone_b},m6b{suffix}@example.com,,Pune\n"
    )

    # C1 — INSPECT + UNDERSTAND: mapping explanation
    status, _h, raw = cert.call("POST", "/api/v1/data/import/preview", payload={
        "content": cust_csv, "content_type": "csv", "target_type": "customer",
    })
    import json as _json
    body = _json.loads(raw) if raw else {}
    data = body.get("data", {})
    colmap = {m["source_column"]: m for m in data.get("column_mapping", [])}
    check("C1 preview accepted (200)", status == 200 and body.get("success") is True,
          f"status={status}")
    check("C2 mapping explained (Client Name → display_name, alias)",
          colmap.get("Client Name", {}).get("target_field") == "display_name"
          and colmap.get("Client Name", {}).get("method") == "alias",
          f"mapping={[(k, v.get('target_field')) for k, v in colmap.items()]}")
    check("C3 every column carries a reason",
          bool(data.get("column_mapping")) and all(m.get("reason") for m in data["column_mapping"]))
    check("C4 preview does not write (valid=2, invalid=0)",
          data.get("valid_records") == 2 and data.get("invalid_records") == 0)

    # C5 — DETECT AMBIGUITY: two name-like columns
    status, _h, raw = cert.call("POST", "/api/v1/data/import/preview", payload={
        "content": "Name,Guest Name,Phone\nX,Y,+1-555-0199\n",
        "content_type": "csv", "target_type": "customer",
    })
    amb = (_json.loads(raw).get("data", {}) if raw else {})
    amb_codes = [a.get("code") for a in amb.get("ambiguities", [])]
    check("C5 ambiguity surfaced (multiple name-like columns)",
          "multiple_candidates" in amb_codes, f"codes={amb_codes}")

    # C6 — CONFIRM + CANONICAL PERSISTENCE
    status, _h, raw = cert.call("POST", "/api/v1/data/import/commit", payload={
        "content": cust_csv, "content_type": "csv", "target_type": "customer",
        "source_name": f"m6_cert_customers_{suffix}.csv",
    })
    commit = (_json.loads(raw).get("data", {}) if raw else {})
    check("C6 commit created 2 customers",
          status == 201 and commit.get("created") == 2,
          f"status={status} created={commit.get('created')}")
    rec_ids = [p.get("record_id") for p in commit.get("provenance", [])]
    check("C7 provenance written per record",
          len(rec_ids) == 2 and all(rec_ids), f"ids={rec_ids}")
    session_id = commit.get("import_session", "")
    check("C8 import session recorded", bool(session_id), f"session={session_id[:8]}…")

    # C9 — FIND IN THE PRODUCT (canonical Relationships surface)
    # Search by the run-unique suffix (a contiguous substring of every name).
    status, _h, raw = cert.call("GET", f"/relationships/api/v1/relationships?q={suffix}&limit=100")
    rels = (_json.loads(raw).get("relationships", []) if raw else [])
    names = [r.get("display_name") for r in rels]
    check("C9 imported customers findable in Relationships (by search)",
          status == 200 and cust_name_a in names and cust_name_b in names,
          f"found={names[:5]}")

    if rec_ids:
        first_id = rec_ids[0]
        # C10 — PROVENANCE
        status, _h, raw = cert.call("GET", f"/api/v1/data/provenance/customer/{first_id}")
        prov = (_json.loads(raw).get("data", {}) if raw else {})
        origin = prov.get("origin") or {}
        check("C10 provenance readable (source, row, session, mapping)",
              status == 200 and prov.get("has_provenance") is True
              and origin.get("source_name") == f"m6_cert_customers_{suffix}.csv"
              and origin.get("row") == 1
              and origin.get("import_session") == session_id
              and origin.get("field_mapping", {}).get("display_name") == "Client Name",
              f"origin={ {k: origin.get(k) for k in ('source_name', 'row', 'imported_by')} }")

        # C11 — CORRECTION
        status, _h, raw = cert.call("POST", "/api/v1/data/import/correct", payload={
            "target_type": "customer", "record_id": first_id,
            "field": "city", "new_value": "Mumbai City",
            "reason": "M6 runtime proof correction",
        })
        corr = (_json.loads(raw).get("data", {}) if raw else {})
        check("C11 correction applied with audit",
              status == 200 and corr.get("ok") is True
              and corr.get("correction", {}).get("old_value") == "Delhi"
              and corr.get("correction", {}).get("corrected_by") == CERT_IDENTITY,
              f"status={status}")
        status, _h, raw = cert.call("GET", f"/api/v1/data/provenance/customer/{first_id}")
        prov2 = (_json.loads(raw).get("data", {}) if raw else {})
        check("C12 correction visible in provenance trail",
              len(prov2.get("corrections") or []) == 1
              and prov2["corrections"][0].get("field") == "city")

    # C13 — DUPLICATE RESOLUTION (idempotent re-commit)
    status, _h, raw = cert.call("POST", "/api/v1/data/import/commit", payload={
        "content": cust_csv, "content_type": "csv", "target_type": "customer",
        "source_name": f"m6_cert_customers_{suffix}.csv",
    })
    dup = (_json.loads(raw).get("data", {}) if raw else {})
    check("C13 re-import is an idempotent no-op (no duplicates)",
          dup.get("status") == "noop" and dup.get("created") == 0
          and dup.get("duplicates_skipped") == 2,
          f"status={dup.get('status')} created={dup.get('created')}")

    # C14 — FAILURE + RECOVERY (deliberately induced)
    status, _h, raw = cert.call("POST", "/api/v1/data/import/commit", payload={
        "content": "not parseable json", "content_type": "json", "target_type": "customer",
    })
    fail = (_json.loads(raw).get("data", {}) if raw else {})
    check("C14 induced failure is truthful (no fake success)",
          fail.get("status") == "rejected" and fail.get("created") == 0,
          f"status={fail.get('status')}")
    status, _h, raw = cert.call("POST", "/api/v1/data/import/commit", payload={
        "content": f"Client Name,Email\nM6 Cert Kavya {suffix},m6k{suffix}@example.com\n",
        "content_type": "csv", "target_type": "customer",
    })
    rec = (_json.loads(raw).get("data", {}) if raw else {})
    check("C15 recovery after failure (import succeeds)",
          status == 201 and rec.get("created") == 1, f"status={status}")

    # ═══════════════════════════════════════════════════════════════════
    # SUPPLIER INGESTION
    # ═══════════════════════════════════════════════════════════════════
    sup_name = f"M6 Cert Sundara {suffix}"
    sup_csv = (
        "Vendor Name,Type,Contact Person,Email,City,Payment Terms\n"
        f"{sup_name},hotel,Priya Sharma,sup{suffix}@example.com,Goa,Net 30\n"
    )
    status, _h, raw = cert.call("POST", "/api/v1/data/import/preview", payload={
        "content": sup_csv, "content_type": "csv", "target_type": "supplier",
    })
    sup_preview = (_json.loads(raw).get("data", {}) if raw else {})
    sup_colmap = {m["source_column"]: m for m in sup_preview.get("column_mapping", [])}
    check("S1 supplier mapping explained (Vendor Name → name)",
          sup_colmap.get("Vendor Name", {}).get("target_field") == "name",
          f"mapping={[(k, v.get('target_field')) for k, v in sup_colmap.items()]}")

    status, _h, raw = cert.call("POST", "/api/v1/data/import/commit", payload={
        "content": sup_csv, "content_type": "csv", "target_type": "supplier",
        "source_name": f"m6_cert_suppliers_{suffix}.csv",
    })
    sup_commit = (_json.loads(raw).get("data", {}) if raw else {})
    check("S2 supplier committed", status == 201 and sup_commit.get("created") == 1,
          f"status={status} created={sup_commit.get('created')} "
          f"errors={str(sup_commit.get('errors'))[:220]}")
    sup_ids = [p.get("record_id") for p in sup_commit.get("provenance", [])]
    if sup_ids:
        status, _h, raw = cert.call("GET", f"/api/v1/data/provenance/supplier/{sup_ids[0]}")
        sprov = (_json.loads(raw).get("data", {}) if raw else {})
        check("S3 supplier provenance readable",
              status == 200 and (sprov.get("origin") or {}).get("source_name") == f"m6_cert_suppliers_{suffix}.csv")
        status, _h, raw = cert.call("POST", "/api/v1/data/import/correct", payload={
            "target_type": "supplier", "record_id": sup_ids[0],
            "field": "city", "new_value": "Panaji", "reason": "M6 runtime proof",
        })
        scor = (_json.loads(raw).get("data", {}) if raw else {})
        check("S4 supplier correction applied", status == 200 and scor.get("ok") is True,
              f"status={status}")

    # S5 — SIMILAR NAME (surface, never merge): seed-like check via preview
    status, _h, raw = cert.call("POST", "/api/v1/data/import/preview", payload={
        "content": f"name,category\n{sup_name.replace('Sundara', 'Sundaraa')},hotel\n",
        "content_type": "csv", "target_type": "supplier",
    })
    sim = (_json.loads(raw).get("data", {}) if raw else {})
    sim_rec = (sim.get("records") or [{}])[0]
    check("S5 similar supplier surfaced (never merged)",
          sim_rec.get("identity_action") == "create" and bool(sim_rec.get("similar_candidates")),
          f"candidates={[c.get('name') for c in (sim_rec.get('similar_candidates') or [])]}")

    # ═══════════════════════════════════════════════════════════════════
    # ISOLATION
    # ═══════════════════════════════════════════════════════════════════
    anon = Http(BASE)
    status, _h, _b = anon.call("GET", "/api/v1/data/provenance/customer/1", follow=False)
    check("X1 anonymous provenance refused (401/302)", status in (401, 302), f"status={status}")

    # Cross-tenant at the app level — production app object, real second tenant
    from app import create_app
    from app.models import OrgMember

    founder_ident = "sid_a3cd655b1e6f4b0f9c1113ba7ec26d41"
    app = create_app()
    with app.app_context():
        membership = (OrgMember.query
                      .filter_by(identity_id=founder_ident, is_active=True)
                      .order_by(OrgMember.organization_id)
                      .first())
        second_org = membership.organization_id if membership else None
    check("X2 second real tenant resolved", second_org is not None and second_org != CERT_ORG,
          f"org={second_org}")
    if rec_ids and second_org and second_org != CERT_ORG:
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["identity_id"] = founder_ident
            sess["user_id"] = founder_ident
            sess["current_org_id"] = second_org
        resp = client.get(f"/api/v1/data/provenance/customer/{rec_ids[0]}")
        check("X3 other tenant cannot READ provenance (404)", resp.status_code == 404,
              f"status={resp.status_code}")
        resp = client.post("/api/v1/data/import/correct", json={
            "target_type": "customer", "record_id": rec_ids[0],
            "field": "display_name", "new_value": "Hijacked",
        })
        check("X4 other tenant cannot CORRECT (404)", resp.status_code == 404,
              f"status={resp.status_code}")

    print(f"\nRESTART_SURVIVAL_RECORD_IDS=customer:{rec_ids} supplier:{sup_ids}")
    print(f"IMPORT_SESSION={session_id}")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
