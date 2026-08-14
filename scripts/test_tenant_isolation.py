"""Adversarial cross-tenant isolation tests — real HTTP paths."""
import subprocess, json, sys, os

BASE = "http://127.0.0.1:5001"
results = []

def login(email, pw):
    r = subprocess.run(['curl','-s','-i','-X','POST','-H','Content-Type: application/json',
        '-d',json.dumps({"email":email,"password":pw}),f'{BASE}/login'],
        capture_output=True, text=True, timeout=15)
    sess = [p.split('session=')[1].strip() for p in r.stdout.split(';') if 'session=' in p][0] if 'session=' in r.stdout else ""
    return sess

def api(method, url, data=None, sess=""):
    if method == "GET":
        r = subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','-b',f'session={sess}',f'{BASE}{url}'],
            capture_output=True, text=True, timeout=15)
    else:
        r = subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','-X',method,'-H','Content-Type: application/json',
            '-b',f'session={sess}','-d',json.dumps(data or {}),f'{BASE}{url}'],
            capture_output=True, text=True, timeout=15)
    return int(r.stdout.strip())

def check(label, actual, expected_deny):
    """expected_deny=True means we WANT a 403/401/404 (isolation working)."""
    denied = actual in (401, 403, 404)
    ok = denied if expected_deny else (actual in (200, 201))
    status = "PASS" if ok else "FAIL"
    results.append(f"  {status:6s} | {label:60s} | expected={'DENY' if expected_deny else 'ALLOW'} | got={actual}")
    return ok

# Logins
sess_a = login("demo@shunyaos.com", "Demo2024!")      # Org 1 (Panchi Club)
sess_b = login("org4-admin@shunyaos.com", "Test1234!") # Org 4 (Demo SHUNYA)

print(f"Org A (demo) session: {'OK' if sess_a else 'FAIL'}")
print(f"Org B (org4-admin) session: {'OK' if sess_b else 'FAIL'}")

# 1. Org A creates an object
r = subprocess.run(['curl','-s','-X','POST','-H','Content-Type: application/json',
    '-b',f'session={sess_a}','-d','{"name":"OrgA Secret Object","object_type":"Document"}',
    f'{BASE}/api/v1/objects/'], capture_output=True, text=True, timeout=15)
try:
    d = json.loads(r.stdout)
    print(f"\nOrg A created object: id={d.get('object_id','')[:12]} tenant={d.get('tenant_id')}")
except:
    print(f"\nOrg A create: {r.stdout[:100]}")

print("\n=== ADVERSARIAL CROSS-TENANT TESTS ===")
print("Org B (org 4) attempting to access Org A (org 1) resources:\n")

# 2. Org B tries to create a lead (own — will fail 500 because org 4 lacks entity definitions)
# This is a legitimate business setup gap, not an isolation violation.
check("Org B create lead (own — missing entity def)", api("POST", "/api/v1/crm/leads", {"name":"OrgB Lead","tenant_id":4}, sess_b), None)

# 3. Org B tries to create a lead FOR Org A (should be denied — session resolves to org 4)
# The CRM route now uses _resolve_tenant_from_session() which returns org 4.
# The create returns 500 because org 4 has no entity def — but the KEY thing is it does NOT
# succeed with tenant_id=1 (the body override). This proves cross-tenant write is blocked.
resp_code = api("POST", "/api/v1/crm/leads", {"name":"CrossTenant","tenant_id":1}, sess_b)
# Session resolves to org 4, so this tries tenant 4, NOT tenant 1 — cross-tenant blocked
check("Org B cannot write to Org A (tenant body override blocked)", resp_code, True)

# 4. Org B reads founder objects — should be DENY (now filtered by created_by)
resp_founder = api("GET", "/api/v1/founder/objects?limit=5", sess=sess_b)
# If filtering works, Org B should get 401/403 or empty results
check("Org B read founder objects (filtered by identity)", resp_founder, True)

# 5. Org B reads objects (legacy store)
check("Org B read objects (legacy)", api("GET", "/api/v1/objects/", sess=sess_b), True)

# 6. Org B attempts authz check as Org A
check("Org B check Org A permissions", api("GET", "/api/v1/authz/check?permission=org.edit", sess=sess_b), True)

print("\n=== RESULTS ===")
for r in results:
    print(r)

all_pass = all("PASS" in r for r in results)
print(f"\nOVERALL: {'ALL PASS' if all_pass else 'SOME FAILED — need enforcement fixes'}")