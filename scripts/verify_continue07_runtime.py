#!/usr/bin/env python3
"""CONTINUE-07 runtime proof — /documents + media asset lifecycle on the
DEPLOYED production build, over real HTTPS with the isolated certification
tenant.

The certification login is read from the 0600 credential file; values are
never printed. Prints PASS/FAIL lines; exits non-zero on any failure.

Usage:
    .venv/bin/python scripts/verify_continue07_runtime.py
"""
import http.cookiejar
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("SHUNYA_PROD_URL", "https://shunyaos.com")
LOGIN_FILE = "/home/shunya-deploy/.shunya/certification_login.txt"
WORKSPACE_ID = "ws_certification"

RESULTS = []


def check(name, ok, detail=None):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}"
          + (f" — {detail}" if detail is not None else ""))


def read_login():
    email = password = None
    with open(LOGIN_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.lower().startswith("email:"):
                email = line.split(":", 1)[1].strip()
            elif line.lower().startswith("password:"):
                password = line.split(":", 1)[1].strip()
    if not email or not password:
        raise SystemExit("credential file not parseable")
    return email, password


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Http:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        handlers = [
            urllib.request.HTTPCookieProcessor(self.jar),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        ]
        self.opener = urllib.request.build_opener(*handlers)
        self.no_redirect = urllib.request.build_opener(
            NoRedirect(), *handlers)

    def call(self, method, path, payload=None, headers=None, follow=True):
        url = self.base + path
        body = None
        hdrs = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=body, headers=hdrs,
                                     method=method)
        opener = self.opener if follow else self.no_redirect
        try:
            resp = opener.open(req, timeout=30)
            return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, method, path, payload=None, headers=None):
        status, _h, body = self.call(method, path, payload, headers)
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = None
        return status, data


def finish() -> int:
    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED: " + "; ".join(failed))
    return 1 if failed else 0


def main() -> int:
    http = Http(BASE)

    # ── 0. Unauthenticated /documents baseline ─────────────────────────
    status, headers, _ = http.call("GET", "/documents", follow=False)
    check("unauthenticated /documents refuses (302)", status == 302,
          f"status={status}")
    check("unauthenticated redirect targets /login",
          "/login" in (headers.get("Location") or ""),
          headers.get("Location"))

    # ── 1. Certification sign-in ───────────────────────────────────────
    # org_id is the deliberate organization selection the sign-in endpoint
    # exposes (an isolated certification tenant).
    email, password = read_login()
    status, body = http.json("POST", "/api/v1/founder/signin",
                             payload={"email": email, "password": password,
                                      "org_id": 278})
    ok = status == 200 and isinstance(body, dict) and body.get("success")
    check("certification sign-in over HTTPS", ok, f"status={status}")
    if not ok:
        return finish()

    auth_headers = {"X-Workspace-Id": WORKSPACE_ID}
    identity_id = body.get("identity_id") or ""
    if identity_id:
        auth_headers["X-Identity-Id"] = identity_id

    # ── 2. /documents — the CONTINUE-07 fix ────────────────────────────
    status, headers, raw = http.call("GET", "/documents")
    text = raw.decode("utf-8", "replace")
    check("authenticated /documents serves 200 (no 500)", status == 200,
          f"status={status}")
    check("/documents is the SPA shell, not an error page",
          "SHUNYA" in text.upper()
          and "TemplateNotFound" not in text
          and "Internal Server Error" not in text)
    check("/documents content-type is html",
          "text/html" in (headers.get("Content-Type") or ""),
          headers.get("Content-Type"))

    # ── 3. Document deep link ──────────────────────────────────────────
    status, _headers, raw = http.call("GET", "/documents/424242")
    text = raw.decode("utf-8", "replace")
    check("authenticated /documents/<id> serves the SPA shell (no crash)",
          status == 200 and "SHUNYA" in text.upper(), f"status={status}")

    # ── 4. Document API ────────────────────────────────────────────────
    status, body = http.json("GET", "/api/v1/workspace/documents?limit=5",
                             headers=auth_headers)
    check("authenticated document API 200", status == 200, f"status={status}")

    # ── 5. Media lifecycle through the real API ────────────────────────
    status, body = http.json("POST", "/api/v1/media/generate",
                             payload={
                                 "prompt": "CONTINUE-07 runtime proof asset",
                                 "platform": "instagram-square",
                                 "aspect_ratio": "1:1",
                                 "visual_style": "realistic",
                             },
                             headers=auth_headers)
    asset = (body or {}).get("data") or {}
    asset_id = asset.get("id") or asset.get("asset_id")
    check("media generate 200 + asset persisted", status == 200 and asset_id,
          f"status={status}, error={(body or {}).get('error')}, "
          f"runtime_state={asset.get('runtime_state')}")
    if not asset_id:
        return finish()

    status, body = http.json(
        "PATCH", f"/api/v1/media/assets/{asset_id}/rename",
        payload={"name": "CONTINUE-07 renamed"}, headers=auth_headers)
    renamed = ((body or {}).get("data") or {}).get("raw_prompt")
    check("rename 200 + persisted", status == 200
          and renamed == "CONTINUE-07 renamed", f"status={status}, name={renamed}")

    status, body = http.json("POST", f"/api/v1/media/assets/{asset_id}/archive",
                             headers=auth_headers)
    check("archive 200", status == 200, f"status={status}")

    # State guard: trash while archived must fail (guard, not success)
    status, _body = http.json("POST", f"/api/v1/media/assets/{asset_id}/trash",
                              headers=auth_headers)
    check("state guard: trash-while-archived refused", status >= 400,
          f"status={status}")

    status, _body = http.json("POST", f"/api/v1/media/assets/{asset_id}/restore",
                              headers=auth_headers)
    check("restore-from-archive 200", status == 200, f"status={status}")

    status, _body = http.json("POST", f"/api/v1/media/assets/{asset_id}/trash",
                              headers=auth_headers)
    check("trash 200", status == 200, f"status={status}")

    status, _body = http.json("POST", f"/api/v1/media/assets/{asset_id}/restore",
                              headers=auth_headers)
    check("restore-from-trash 200", status == 200, f"status={status}")

    status, _body = http.json("POST", f"/api/v1/media/assets/{asset_id}/trash",
                              headers=auth_headers)
    check("trash (final) 200", status == 200, f"status={status}")

    status, _body = http.json(
        "DELETE", f"/api/v1/media/assets/{asset_id}/permanent-delete",
        headers=auth_headers)
    check("permanent delete 200", status == 200, f"status={status}")

    status, _body = http.json("GET", f"/api/v1/media/assets/{asset_id}",
                              headers=auth_headers)
    check("permanent delete is irreversible (asset gone: 404)", status == 404,
          f"status={status}")

    # ── 6. Unauthorized behavior on a real endpoint ────────────────────
    anon = Http(BASE)
    status, _h, _b = anon.call("GET", "/api/v1/media/assets", follow=False)
    check("unauthenticated media API fails closed (401/302)",
          status in (401, 302), f"status={status}")

    return finish()


if __name__ == "__main__":
    sys.exit(main())
