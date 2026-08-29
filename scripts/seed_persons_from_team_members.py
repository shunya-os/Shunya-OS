"""
Seed Person records from existing TeamMembers.

Creates a canonical Person record for each TeamMember that doesn't already
have one (person_id is NULL). Links the Person record back to the TeamMember.
"""

import sys
import os

# Ensure we can import from the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.auth import TeamMember
from app.models import Person

app = create_app()

with app.app_context():
    created = 0
    skipped = 0
    errors = 0

    team_members = TeamMember.query.all()
    print(f"Found {len(team_members)} TeamMembers")

    for tm in team_members:
        if tm.person_id is not None:
            person = db.session.get(Person, tm.person_id)
            if person:
                print(f"  SKIP: TM #{tm.id} ({tm.email}) already linked to Person #{tm.person_id}")
                skipped += 1
                continue

        # Check if a Person already exists with the same email as canonical_name
        existing = Person.query.filter_by(canonical_name=tm.email).first()
        if existing:
            print(f"  LINK: TM #{tm.id} ({tm.email}) → existing Person #{existing.id}")
            tm.person_id = existing.id
            db.session.add(tm)
            created += 1
            continue

        # Create a new Person
        try:
            person = Person(
                tenant_id=tm.tenant_id,
                name=tm.name,
                canonical_name=tm.email,
                preferred_name=tm.name.split()[0] if tm.name else tm.email.split("@")[0],
                status="active",
            )
            db.session.add(person)
            db.session.flush()  # Get person.id
            tm.person_id = person.id
            db.session.add(tm)
            print(f"  CREATE: Person #{person.id} '{person.canonical_name}' ← TM #{tm.id}")
            created += 1
        except Exception as e:
            db.session.rollback()
            print(f"  ERROR: TM #{tm.id} ({tm.email}): {e}")
            errors += 1

    db.session.commit()

    print(f"\nDone: {created} created/linked, {skipped} skipped, {errors} errors")
    print(f"TeamMembers: {TeamMember.query.count()}")
    print(f"Persons: {Person.query.count()}")