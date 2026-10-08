#!/usr/bin/env python3
"""CONTINUE-08 runtime proof — attention chain on the DEPLOYED build.

A) REAL business event in the certification tenant through the canonical
   IngestionService → EventBus → attention subscriber → AttentionItem
   (production app object + production database; no UI access involved).
B) Over HTTPS: the certification session sees the item; anonymous is refused;
   the FOUNDER session (a different tenant) can neither read nor resolve it;
   the certification session resolves it and the active list reflects truth.
C) A restart-survival item is left ACTIVE for the next deploy's restart to
   verify.

Credential values are read from 0600 files and never printed.
"""
import os
import sys
import time
import json

sys.path.insert(0, "/home/shunya-deploy/shunya_os")
os.environ.setdefault("SHUNYA_ENVIRONMENT", "production")

sys.path.insert(0, "/home/shunya-deploy/shunya_os/scripts")
from verify_continue07_runtime import Http, read_login, BASE, WORKSPACE_ID  # noqa: E402

CERT_ORG = 278
CERT_IDENTITY = "sid_5ef358418d4246ba8e156de0"
FOUNDER_FILE = "/home/shunya-deploy/.shunya/founder-credential.txt"

RESULTS = []


def check(name, ok, detail=None):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}"
          + (f" — {detail}" if detail is not None else ""))


def read_kv(path, keys):
    """Tolerant 'Key: value' parser. Values never printed."""
    wanted = {k.lower(): None for k in keys}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            if key in wanted:
                wanted[key] = value.strip()
    return wanted


def finish() -> int:
    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED: " + "; ".join(failed))
    return 1 if failed else 0


def main() -> int:
    # ── Part A: real ingestion events in the cert tenant ────────────────
    from app import create_app, db
    from core.ingestion import IngestionRecord, InformationClass, SourceType
    from core.ingestion.service import IngestionService
    from app.attention.models import AttentionItem, AttentionSource

    stamp = int(time.time())
    ing_review = f"ing_continue08_review_{stamp}"
    ing_restart = f"ing_continue08_restart_{stamp}"

    app = create_app()
    with app.app_context():
        service = IngestionService()
        result = service.process(IngestionRecord(
            ingestion_id=ing_review,
            tenant_id=CERT_ORG,
            source=SourceType.CSV,
            source_identity=CERT_IDENTITY,
            normalized_payload={"name": "CONTINUE-08 review probe"},
            information_class=InformationClass.USER_PROVIDED,
        ))
        check("A1 canonical event published by IngestionService",
              bool(result.canonical_event_id),
              f"event={result.canonical_event_id}")

        item = AttentionItem.query.filter_by(
            organization_id=CERT_ORG,
            source=AttentionSource.EVENT.value,
            related_object_id=ing_review,
        ).first()
        check("A2 AttentionItem persisted from the event (no UI access)",
              item is not None,
              f"item_id={item.id if item else None}")
        if item is None:
            return finish()
        check("A3 item carries canonical owner",
              item.identity_id == CERT_IDENTITY and item.organization_id == CERT_ORG,
              f"identity={item.identity_id} org={item.organization_id}")
        check("A4 item provenance links the event",
              (item.provenance or {}).get("method") == "attention_event_subscriber",
              f"provenance={json.dumps(item.provenance or {})[:180]}")

        # Restart-survival item (left ACTIVE for the next deploy restart)
        service.process(IngestionRecord(
            ingestion_id=ing_restart,
            tenant_id=CERT_ORG,
            source=SourceType.CSV,
            source_identity=CERT_IDENTITY,
            normalized_payload={"name": "CONTINUE-08 restart probe"},
            information_class=InformationClass.USER_PROVIDED,
        ))
        restart_item = AttentionItem.query.filter_by(
            organization_id=CERT_ORG,
            source=AttentionSource.EVENT.value,
            related_object_id=ing_restart,
        ).first()
        check("A5 restart-survival item created (left active)",
              restart_item is not None,
              f"restart_item_id={restart_item.id if restart_item else None}")

        item_id = item.id
        restart_item_id = restart_item.id if restart_item else None

    print(f"REVIEW_ITEM_ID={item_id}")
    print(f"RESTART_ITEM_ID={restart_item_id}")

    # ── Part B: HTTPS — visibility, isolation, resolve ──────────────────
    cert = Http(BASE)
    email, password = read_login()
    status, body = cert.json("POST", "/api/v1/founder/signin",
                             payload={"email": email, "password": password,
                                      "org_id": CERT_ORG})
    ok = status == 200 and isinstance(body, dict) and body.get("success")
    check("B0 certification sign-in", ok, f"status={status}")
    if not ok:
        return finish()
    cert_headers = {"X-Workspace-Id": WORKSPACE_ID}
    if body.get("identity_id"):
        cert_headers["X-Identity-Id"] = body["identity_id"]

    # Attention items raised from ingestion events are organization-level
    # (the ingestion record carries no workspace id). Query them without the
    # workspace filter — the header is deliberately omitted for these calls.
    attention_headers = {k: v for k, v in cert_headers.items()
                         if k != "X-Workspace-Id"}

    status, body = cert.json("GET", "/api/v1/attention/",
                             headers=attention_headers)
    ids = [i.get("id") for i in (body or {}).get("data", [])] if body else []
    check("B1 certification session sees the event-sourced item",
          status == 200 and item_id in ids,
          f"status={status} active_ids={ids}")

    anon = Http(BASE)
    status, _h, _b = anon.call("GET", "/api/v1/attention/", follow=False)
    check("B2 anonymous access refused (401/302)", status in (401, 302),
          f"status={status}")

    fk = read_kv(FOUNDER_FILE, ["Email", "Password"])
    if fk.get("email") and fk.get("password"):
        founder = Http(BASE)
        status, body = founder.json("POST", "/api/v1/founder/signin",
                                    payload={"email": fk["email"],
                                             "password": fk["password"]})
        fok = status == 200 and isinstance(body, dict) and body.get("success")
        check("B3 founder HTTPS sign-in (archived credential file)", fok,
              f"status={status} — archived file did not authenticate"
              if not fok else "ok")
    else:
        check("B3 founder credential file parseable", False, "keys missing")

    # Cross-tenant negative proof at the app level (the same production app
    # object and database the live service uses): a REAL second identity and
    # its REAL organization must be refused by the same route code paths.
    from app.models import OrgMember
    founder_ident = "sid_a3cd655b1e6f4b0f9c1113ba7ec26d41"
    with app.app_context():
        membership = (OrgMember.query
                      .filter_by(identity_id=founder_ident, is_active=True)
                      .order_by(OrgMember.organization_id)
                      .first())
        second_org = membership.organization_id if membership else None
    check("B3b second real tenant resolved (app level)",
          second_org is not None and second_org != CERT_ORG,
          f"org={second_org}")
    if second_org and second_org != CERT_ORG:
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["identity_id"] = founder_ident
            sess["user_id"] = founder_ident
            sess["current_org_id"] = second_org
        resp = client.get(f"/api/v1/attention/{item_id}")
        detail = (resp.get_json() or {}).get("detail", (resp.get_json() or {}).get("error"))
        check("B4 other tenant cannot READ the item (403)",
              resp.status_code == 403, f"status={resp.status_code} detail={detail}")
        resp = client.post(f"/api/v1/attention/{item_id}/resolve")
        detail = (resp.get_json() or {}).get("detail", (resp.get_json() or {}).get("error"))
        check("B5 other tenant cannot RESOLVE the item (403)",
              resp.status_code == 403, f"status={resp.status_code} detail={detail}")

    status, body = cert.json("POST", f"/api/v1/attention/{item_id}/resolve",
                             headers=cert_headers)
    check("B6 certification session resolves the item",
          status == 200 and (body or {}).get("data", {}).get("state") == "resolved",
          f"status={status}")

    status, body = cert.json("GET", "/api/v1/attention/",
                             headers=attention_headers)
    ids = [i.get("id") for i in (body or {}).get("data", [])] if body else []
    check("B7 resolved item leaves the active list (truth after action)",
          item_id not in ids, f"active_ids={ids}")

    status, body = cert.json("GET", f"/api/v1/attention/{item_id}",
                             headers=cert_headers)
    check("B8 resolved item remains auditable (state=resolved)",
          status == 200 and (body or {}).get("data", {}).get("state") == "resolved",
          f"status={status}")

    return finish()


if __name__ == "__main__":
    sys.exit(main())
