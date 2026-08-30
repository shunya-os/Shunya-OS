"""
§5 — Document enrichment pipeline: entity → identity → relationship → knowledge.

Connects extracted document entities to canonical Person records,
creates Person records for unknown entities, builds relationships,
and populates knowledge_entries/knowledge_documents for AI retrieval.

Run after extraction_pipeline.store_document_facts() has generated knowledge_facts.
"""
import json
import logging
import re
from datetime import datetime, timezone
from app import db
from app.models import Document, Person
from app.shunya.knowledge_store import ImmutableKnowledgeStore

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Normalize a person name for matching."""
    return re.sub(r"\s+", " ", name.strip().lower())


def _find_or_create_person(name: str, email: str = "", confidence: float = 0.5) -> Person | None:
    """Find an existing Person by name, or create a new one."""
    normalized = _normalize_name(name)

    # Try exact match first
    existing = Person.query.filter(Person.name.ilike(name.strip())).first()
    if existing:
        return existing

    # Try normalized match
    all_persons = Person.query.all()
    for p in all_persons:
        if _normalize_name(p.name) == normalized:
            return p

    # Create new Person
    person = Person(
        name=name.strip(),
        email=email or "",
        phone="",
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(person)
    db.session.flush()
    return person


def enrich_document_facts(doc_id: int) -> dict:
    """Enrich a document's extracted facts into Person + Relationship + Knowledge records."""
    from app.shunya.knowledge_store.sql_repository import SqlKnowledgeRepository
    from app.models import Relationship

    doc = Document.query.filter(Document.id == doc_id).first()
    if not doc:
        return {"error": f"Document {doc_id} not found"}

    repo = SqlKnowledgeRepository(session=db.session)

    # Get all facts for this document
    facts = repo.get_facts_by_domain("documents")

    persons_created = 0
    persons_matched = 0
    relationships_created = 0
    knowledge_entries_created = 0

    for fact_key, fact in facts.items():
        if not fact_key.startswith(f"document.{doc_id}."):
            continue

        # Parse entity type from fact_key: document.{doc_id}.{entity_type}.{name}
        parts = fact_key.split(".")
        if len(parts) < 4:
            continue

        entity_type = parts[2]
        value = fact.get("value", "")

        if entity_type == "person" and value:
            # Create or find Person
            person = _find_or_create_person(str(value), confidence=fact.get("confidence", 0.5))
            if person:
                doc_id_int = Person.query.filter_by(name=person.name).count()
                if doc_id_int <= 1 and person.email == "":
                    persons_created += 1
                else:
                    persons_matched += 1

                # Create Relationship: Document → Person
                existing_rel = Relationship.query.filter_by(
                    source_id=f"doc_{doc_id}",
                    target_id=str(person.id),
                    type="mentions"
                ).first()
                if not existing_rel:
                    rel = Relationship(
                        source_type="document",
                        source_id=f"doc_{doc_id}",
                        target_type="person",
                        target_id=str(person.id),
                        type="mentions",
                        context=fact.get("evidence", ""),
                        confidence=fact.get("confidence", 0.5),
                        created_at=datetime.now(timezone.utc),
                    )
                    db.session.add(rel)
                    relationships_created += 1

        elif entity_type == "organization" and value:
            # Create Relationship: Document → Organization
            org_name = str(value)
            existing_rel = Relationship.query.filter_by(
                source_id=f"doc_{doc_id}",
                target_id=org_name,
                type="mentions"
            ).filter_by(source_type="document", target_type="organization").first()
            if not existing_rel:
                rel = Relationship(
                    source_type="document",
                    source_id=f"doc_{doc_id}",
                    target_type="organization",
                    target_id=org_name,
                    type="mentions",
                    context=fact.get("evidence", ""),
                    confidence=fact.get("confidence", 0.5),
                    created_at=datetime.now(timezone.utc),
                )
                db.session.add(rel)
                relationships_created += 1

    # Also populate knowledge_entries from facts
    from app.models import KnowledgeEntry
    for fact_key, fact in facts.items():
        if not fact_key.startswith(f"document.{doc_id}."):
            continue

        existing_entry = KnowledgeEntry.query.filter_by(key=fact_key).first()
        if not existing_entry:
            entry = KnowledgeEntry(
                key=fact_key,
                value=str(fact.get("value", "")),
                domain="documents",
                category=fact.get("category", "document.extraction"),
                value_type="text",
                confidence=fact.get("confidence", 0.5),
                evidence=fact.get("evidence", ""),
                source="document_extraction",
                provenance=json.dumps({
                    "document_id": doc_id,
                    "fact_key": fact_key,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                }),
                created_by="document_pipeline",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(entry)
            knowledge_entries_created += 1

    db.session.commit()

    return {
        "doc_id": doc_id,
        "persons_created": persons_created,
        "persons_matched": persons_matched,
        "relationships_created": relationships_created,
        "knowledge_entries_created": knowledge_entries_created,
    }


def enrich_all_documents() -> dict:
    """Run enrichment on all documents with extracted text."""
    docs = Document.query.filter(Document.extracted_text.isnot(None)).filter(
        Document.extracted_text != ""
    ).order_by(Document.id).all()

    results = {
        "total_docs": len(docs),
        "processed": 0,
        "total_persons_created": 0,
        "total_persons_matched": 0,
        "total_relationships": 0,
        "total_knowledge_entries": 0,
        "errors": [],
    }

    for doc in docs:
        try:
            r = enrich_document_facts(doc.id)
            results["processed"] += 1
            results["total_persons_created"] += r.get("persons_created", 0)
            results["total_persons_matched"] += r.get("persons_matched", 0)
            results["total_relationships"] += r.get("relationships_created", 0)
            results["total_knowledge_entries"] += r.get("knowledge_entries_created", 0)
        except Exception as e:
            results["errors"].append({"doc_id": doc.id, "error": str(e)})
            db.session.rollback()

    logger.info(
        "Enrichment complete: processed=%d/%d, persons=%d(+%d matched), rels=%d, entries=%d",
        results["processed"], results["total_docs"],
        results["total_persons_created"], results["total_persons_matched"],
        results["total_relationships"], results["total_knowledge_entries"],
    )
    return results