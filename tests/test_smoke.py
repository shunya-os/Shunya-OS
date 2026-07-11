#!/usr/bin/env python3
"""Quick functional test for Shunya OS."""
import sys, os
os.environ.setdefault("FLASK_ENV", "development")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app("development")

errors = []

with app.test_client() as c:
    # 1. Health
    r = c.get("/health")
    if r.status_code != 200:
        errors.append(f"Health check: {r.status_code}")

    # 2. Login page
    r = c.get("/auth/login")
    if r.status_code not in (200, 302):
        errors.append(f"Login page: {r.status_code}")

    # 3. Signup page
    r = c.get("/auth/signup")
    if r.status_code not in (200, 302):
        errors.append(f"Signup page: {r.status_code}")

    # 4. Login
    r = c.post("/auth/login/password", json={"email": "rajat@panchi.club", "password": "demo123"})
    if not r.get_json().get("success"):
        errors.append(f"Login failed: {r.get_json()}")

    # 5. Dashboard
    r = c.get("/")
    if r.status_code != 200:
        errors.append(f"Dashboard: {r.status_code}")

    # 6. Entity list
    for etype in ["lead", "patient"]:
        r = c.get(f"/entities/{etype}")
        if r.status_code not in (200, 302):
            errors.append(f"Entity list {etype}: {r.status_code}")

    # 7. Create entity
    r = c.post("/entities/lead/new", data={
        "customer_name": "Test Family",
        "destination": "Goa",
        "phone": "+919999999999"
    })
    if r.status_code not in (200, 302):
        errors.append(f"Create lead: {r.status_code}")

    # 8. Settings
    r = c.get("/settings")
    if r.status_code != 200:
        errors.append(f"Settings: {r.status_code}")

    # 9. Session management
    r = c.get("/auth/sessions")
    if r.status_code != 200:
        errors.append(f"Sessions page: {r.status_code}")

    # 10. Create entity type via API
    r = c.post("/settings/entity-types", json={
        "type": "test_entity",
        "label": "Test",
        "schema": '[{"name":"name","label":"Name","type":"text"}]',
        "statuses": '["new","done"]'
    })
    if r.status_code not in (200, 201, 302, 409):
        errors.append(f"Create entity type: {r.status_code}")

    # 11. API endpoints
    r = c.get("/api/entities/lead")
    if r.status_code not in (200, 401):
        errors.append(f"API list: {r.status_code}")

    r = c.post("/api/webhook/test", json={"test": True})
    if r.status_code != 200:
        errors.append(f"Webhook: {r.status_code}")

print(f"\n{'='*40}")
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED ✓")
    print("  ✓ Health check")
    print("  ✓ Login page")
    print("  ✓ Signup page")
    print("  ✓ Login")
    print("  ✓ Dashboard")
    print("  ✓ Entity lists (lead, patient)")
    print("  ✓ Create entity")
    print("  ✓ Settings")
    print("  ✓ Session management")
    print("  ✓ Entity type creation")
    print("  ✓ API endpoints")
    sys.exit(0)
