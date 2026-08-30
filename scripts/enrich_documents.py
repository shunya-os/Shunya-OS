"""
§5 — Document enrichment: entity → Person → Relationship pipeline.

Connects extracted document entities to Person records, creating Person records
for extracted names, and building Relationship entries.

Run: PYTHONPATH=. python3 scripts/enrich_documents.py
"""
import json, logging, re
from datetime import datetime, timezone
from app import create_app, db
from sqlalchemy import text

logger = logging.getLogger(__name__)


def run():
    app = create_app()
    with app.app_context():
        print("=== §5 Document Enrichment ===")

        # 1. Get all knowledge_facts of type 'person'
        facts = db.session.execute(
            text("SELECT id, fact_key, value, confidence, evidence FROM knowledge_facts WHERE fact_key LIKE 'document.%.person.%'")
        ).fetchall()

        print(f"Found {len(facts)} person facts")

        # Get a valid tenant_id for FK constraints
        first_tenant = db.session.execute(
            text("SELECT id FROM tenants ORDER BY id LIMIT 1")
        ).fetchone()
        default_tenant_id = first_tenant[0] if first_tenant else 1

        persons_created = 0
        persons_matched = 0
        relationships_created = 0

        for fact in facts:
            value = fact.value
            if not value:
                continue

            # Extract doc_id from fact_key: document.{doc_id}.person.{name}
            parts = fact.fact_key.split(".")
            doc_id = parts[1] if len(parts) > 1 else None

            # Clean the name — truncate at known suffix words
            cleaned_value = value.strip()
            for suffix in [" Number", "  ", " of "]:
                idx = cleaned_value.find(suffix)
                if idx > 0:
                    cleaned_value = cleaned_value[:idx].strip()
            if len(cleaned_value) < 3 or cleaned_value.lower() in {"guest", "the", "this", "note", "total", "booking", "payment", "address", "property", "number", "reference", "cancellation", "arrival", "departure"}:
                continue
            value = cleaned_value

            # Check if Person already exists with this name
            existing = db.session.execute(
                text("SELECT id, name FROM persons WHERE LOWER(name) = LOWER(:name) LIMIT 1"),
                {"name": value}
            ).fetchone()

            person_id = None
            if existing:
                persons_matched += 1
                person_id = existing[0]
            else:
                # Create new Person with tenant_id
                result = db.session.execute(
                    text("""INSERT INTO persons (name, email, phone, tenant_id, status, created_at)
                            VALUES (:name, '', '', :tid, 'active', :now)
                            RETURNING id"""),
                    {"name": value, "tid": default_tenant_id, "now": datetime.now(timezone.utc)}
                )
                person_id = result.fetchone()[0]
                persons_created += 1
                print(f"  Created Person: {value} (id={person_id})")

            # Create person_identity link to document
            if doc_id:
                identity_link = f"doc_{doc_id}"
                existing_ident = db.session.execute(
                    text("SELECT id FROM person_identities WHERE person_id = :pid AND identity_type = 'document' AND identity_value = :val LIMIT 1"),
                    {"pid": person_id, "val": identity_link}
                ).fetchone()
                if not existing_ident:
                    db.session.execute(
                        text("""INSERT INTO person_identities (person_id, identity_type, identity_value, normalized_value, source, confidence)
                                VALUES (:pid, 'document', :val, :norm, 'document_extraction', :conf)"""),
                        {"pid": person_id, "val": identity_link, "norm": identity_link, "conf": fact.confidence or 0.5}
                    )

            # Create relationship entry (document → person)
            if doc_id and person_id:
                existing_rel = db.session.execute(
                    text("SELECT id FROM relationships WHERE source = :src AND person_id = :pid AND relationship_type = 'document_mention' LIMIT 1"),
                    {"src": f"doc_{doc_id}", "pid": person_id}
                ).fetchone()
                if not existing_rel:
                    db.session.execute(
                        text("""INSERT INTO relationships (tenant_id, person_id, display_name, email, source, relationship_type, created_at)
                                VALUES (:tid, :pid, :name, '', :src, 'document_mention', :now)"""),
                        {"tid": default_tenant_id, "pid": person_id, "name": value, "src": f"doc_{doc_id}", "now": datetime.now(timezone.utc)}
                    )
                    relationships_created += 1

        db.session.commit()

        print(f"\nResults:")
        print(f"  Persons matched: {persons_matched}")
        print(f"  Persons created: {persons_created}")
        print(f"  Relationships created: {relationships_created}")

        # Summary
        after_persons = db.session.execute(text("SELECT COUNT(*) FROM persons")).scalar()
        after_rels = db.session.execute(text("SELECT COUNT(*) FROM relationships")).scalar()
        after_pi = db.session.execute(text("SELECT COUNT(*) FROM person_identities")).scalar()
        print(f"\nTotal persons: {after_persons}")
        print(f"Total relationships: {after_rels}")
        print(f"Total person_identities: {after_pi}")


if __name__ == "__main__":
    run()