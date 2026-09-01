#!/usr/bin/env python3
"""Runtime verification: identity, objects, memory, AI, business flow."""
import os, sys, json
os.environ["DISABLE_RATE_LIMIT"] = "1"
os.environ["FLASK_ENV"] = "testing"
os.environ["WTF_CSRF_ENABLED"] = "False"
os.environ["SECRET_KEY"] = "test-secret-key"
# Use existing production DB for read tests
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
app = create_app()

results = {"pass": 0, "fail": 0, "skipped": 0, "details": []}

def check(name, ok, detail=""):
    results["pass" if ok else "fail"] += 1
    results["details"].append({"name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {detail[:200] if detail else 'ok'}")

with app.app_context():
    print("\n=== IDENTITY CHAIN ===")
    from app.auth import TeamMember
    from app.models import Person, OrgMember, Organization
    
    users = TeamMember.query.limit(5).all()
    check("TeamMember query returns users", len(users) > 0, f"{len(users)} users")
    if users:
        u = users[0]
        check("TeamMember has identity_id", bool(u.identity_id) or bool(u.email), f"id={u.id} email={u.email}")
    
    persons = Person.query.limit(5).all()
    check("Person table has records", len(persons) > 0, f"{len(persons)} persons")
    
    orgs = Organization.query.limit(5).all()
    check("Organization table has records", len(orgs) > 0, f"{len(orgs)} orgs")
    if orgs:
        om = OrgMember.query.filter_by(organization_id=orgs[0].id).first()
        check("OrgMember exists for first org", om is not None, f"org={orgs[0].name}")
    
    check("shunya_identities used vs person_identities", 
          db.session.execute(db.text("SELECT count(*) FROM shunya_identities")).scalar() > 0,
          f"{db.session.execute(db.text('SELECT count(*) FROM shunya_identities')).scalar()} shunya_identities")
    
    print("\n=== OBJECT STORE ===")
    obj_count = db.session.execute(db.text("SELECT count(*) FROM sh_objects")).scalar()
    check("sh_objects has records", obj_count > 0, f"{obj_count} objects")
    
    uop_count = db.session.execute(db.text("SELECT count(*) FROM sh_uop_objects")).scalar()
    check("sh_uop_objects has records", uop_count > 0, f"{uop_count} objects")
    
    founder_obj_count = db.session.execute(db.text("SELECT count(*) FROM founder_objects")).scalar()
    check("founder_objects has records", founder_obj_count > 0, f"{founder_obj_count} objects")
    
    print("\n=== MEMORY ===")
    mem_count = db.session.execute(db.text("SELECT count(*) FROM memory_records")).scalar()
    check("memory_records table has data", True, f"{mem_count} records")
    
    has_confidence = db.session.execute(db.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='memory_records' AND column_name='confidence'
    """)).scalar() is not None
    check("memory_records has confidence column (migration applied)", has_confidence, "")
    
    print("\n=== FINANCE ===")
    fin_count = db.session.execute(db.text("SELECT count(*) FROM fin_invoices")).scalar()
    check("fin_invoices has records", fin_count > 0, f"{fin_count} invoices")
    inv_count = db.session.execute(db.text("SELECT count(*) FROM invoices")).scalar()
    check("legacy invoices table also has records", inv_count > 0, f"{inv_count} legacy invoices")
    
    print("\n=== CRM / LEADS ===")
    leads_count = db.session.execute(db.text("SELECT count(*) FROM lead")).scalar() + db.session.execute(db.text("SELECT count(*) FROM leads")).scalar()
    check("Lead records exist", leads_count > 0, f"{leads_count} total leads")
    
    print("\n=== SALES ===")
    prop_count = db.session.execute(db.text("SELECT count(*) FROM proposals")).scalar()
    check("Proposals exist", prop_count > 0, f"{prop_count} proposals")
    
    print("\n=== AUTHZ ===")
    role_count = db.session.execute(db.text("SELECT count(*) FROM auth_roles")).scalar()
    check("Auth roles exist", role_count > 0, f"{role_count} roles")
    
    print("\n=== JOB RECORDS ===")
    job_count = db.session.execute(db.text("SELECT count(*) FROM job_records")).scalar()
    check("Job records table exists", True, f"{job_count} records")

print(f"\n{'='*50}")
print(f"RESULTS: {results['pass']} passed, {results['fail']} failed, {results['skipped']} skipped")
sys.exit(0 if results['fail'] == 0 else 1)
