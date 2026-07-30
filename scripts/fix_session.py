"""
Fix session setup for the seeded organization.
Run this to set up sessions properly for all test users.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['DATABASE_URL'] = 'postgresql://shunya:shunya_os_2024@127.0.0.1:5433/shunya_db'

from app import create_app, db
from app.models import Organization, OrgMember, Department
from app.auth import TeamMember
from flask import session

app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": os.environ['DATABASE_URL'], "SECRET_KEY": "shunya-club-secret-key-2024"})

with app.app_context():
    # Link TeamMember identity_ids to OrgMember identity_ids
    org = Organization.query.filter_by(slug="xyz-company").first()
    org_members = OrgMember.query.filter_by(organization_id=org.id).all()
    
    print(f"Setting up session links for {len(org_members)} members...")
    
    # For each OrgMember, update the corresponding TeamMember's identity link
    for om in org_members:
        tm = TeamMember.query.filter_by(email=om.email).first()
        if tm:
            # The TeamMember has a person_id field - let's use that to link
            if not tm.person_id:
                from app.models import Person
                p = Person.query.filter_by(canonical_name=om.name).first()
                if not p:
                    from app.shunya.identity import normalize_email
                    # Create a person record
                    from app.models import Person, PersonIdentity
                    p = Person(canonical_name=om.name, preferred_name=om.name.split()[0] if om.name else om.name)
                    db.session.add(p)
                    db.session.flush()
                    pi = PersonIdentity(person_id=p.id, identity_type="email", 
                        identity_value=om.email, normalized_value=om.email.lower(),
                        verification_state="verified")
                    db.session.add(pi)
                tm.person_id = p.id
                print(f"  Linked TeamMember {tm.email} -> Person {p.id}")
    
    db.session.commit()
    
    print("\nVerification:")
    # Check that the founder login works
    tm = TeamMember.query.filter_by(email="founder@xyzcompany.com").first()
    if tm and tm.check_password("founder123"):
        print(f"  Founder login: OK (id={tm.id}, person_id={tm.person_id})")
    
    # Print the issuers: the identity_id values in OrgMember are different from TeamMember user_id
    print("\nSession mapping needed:")
    print("  Login sets session['user_id'] = TeamMember.id")
    print("  FOR2 routes need session['identity_id'] = OrgMember.identity_id")
    print("  Workspace routes need session['current_org_id'] = Organization.id")
    
    # The fix: Add a middleware that resolves identity_id from user_id
    # Or add a route that sets both
    
    print("\nTo fix at runtime, we need to update the session. Options:")
    print("  1. Add a middleware in app/__init__.py that resolves identity_id from user_id")
    print("  2. Use the founder signin endpoint which sets identity_id")