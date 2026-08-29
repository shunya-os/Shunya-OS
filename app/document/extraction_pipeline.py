"""SHUNYA — Document Entity Extraction Pipeline.

Extracts structured entities (people, dates, amounts, organizations,
reference numbers, emails, phones) from document extracted_text and
stores them as KnowledgeFact records with provenance back to the source document.

Constitutional rule: Document-derived facts are OBSERVATIONS, not VERIFIED TRUTH.
Every fact carries an evidence field with provenance linking to the source document.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app import db
from app.models import Document
from app.shunya.knowledge_store import ImmutableKnowledgeStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Entity Extraction Patterns
# ---------------------------------------------------------------------------

# People names: capitalized words after relationship labels
_PERSON_PATTERN = re.compile(
    r"(?:Client|Name|Customer|Passenger|Guest|Contact|Passport\s*Name|Lead\s*Guest)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    re.I,
)
# Also capture lines that look like "John Smith" at the start of a line
# Exclude common label words and single-word matches
_PERSON_LINE_PATTERN = re.compile(r"^([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})(?:\s|$)", re.M)

# Monetary amounts
_AMOUNT_PATTERN = re.compile(
    r"(?:₹|Rs\.?\s*|INR\s*|USD\s*|EUR\s*|£)\s*\.?\s*(\d[\d,]*\.?\d*)",
    re.I,
)

# Dates — ISO, US/EU, and named month formats
_DATE_PATTERN = re.compile(
    r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    r"|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}"
    r"|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    re.I,
)

# Email addresses
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Phone numbers
_PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
)

# Reference / ID numbers (Booking ID, Invoice No, Ref, PNR, etc.)
# Require at least one digit in the captured value to avoid matching English words
_REFERENCE_PATTERN = re.compile(
    r"(?:Booking\s*(?:ID|Reference|No|Number)|Invoice\s*(?:#|No|Number)|Ref[.\s:#]*|PNR[:\s]*|Ticket\s*(?:No|Number|#)|Member\s*ID|Reference\s*No)[:\s#]*([A-Z0-9]{4,30})",
    re.I,
)

# Organization / company names — specific labels and known brands
_ORG_PATTERN = re.compile(
    r"(?:Property|Hotel|Company|Organization|Supplier|Provider|Promotion)[:\s]+([A-Z][A-Za-z0-9\s\.&]{3,50})"
    r"|"
    r"(Panchi\.Club|Novotel|Marriott|Hilton|Hyatt|Sheraton|Accor|IHG|Taj|Oberoi|ITC|Bali\s+(?:Eco|Resort|Hotel|Lodge|Villa))",
    re.I,
)

# ---------------------------------------------------------------------------
# Entity Extraction
# ---------------------------------------------------------------------------


def extract_entities(text: str) -> dict[str, list[dict[str, Any]]]:
    """Extract structured entities from document text.

    Returns a dict of entity type -> list of {value, context, confidence} dicts.
    Entity types: persons, amounts, dates, emails, phones, references, organizations.
    """
    if not text or not text.strip():
        return {}

    entities: dict[str, list[dict[str, Any]]] = {}

    # --- People ---
    persons = []
    for m in _PERSON_PATTERN.finditer(text):
        name = m.group(1).strip()
        # Truncate at "Number" or other label-qualifiers that over-grab
        for cutoff in (" Number", "  ", " of "):
            idx = name.find(cutoff)
            if idx > 0:
                name = name[:idx].strip()
        if name and len(name) >= 3:
            persons.append({
                "value": name,
                "context": _snippet(text, m.start(), m.end()),
                "confidence": 0.7,
            })
    for m in _PERSON_LINE_PATTERN.finditer(text):
        val = m.group(1).strip()
        # Deduplicate against already-found names
        if not any(p["value"] == val for p in persons):
            # Skip common false positives (labels, English words, etc.)
            _skip_words = {
                "the", "this", "that", "from", "with", "note", "booking", "please",
                "total", "cancellation", "arrival", "departure", "payment", "visa",
                "property", "address", "remarks", "benefits", "included", "guest",
                "number", "reference", "confirmation", "cancellation policy",
                "payment method", "special requests", "largebed", "all special",
                "booked and", "property contact", "free cancellation",
            }
            if val.lower() not in _skip_words and len(val.split()) >= 2:
                persons.append({
                    "value": val,
                    "context": _snippet(text, m.start(), m.end()),
                    "confidence": 0.5,
                })
    if persons:
        entities["persons"] = persons

    # --- Monetary amounts ---
    amounts = []
    seen_amounts = set()
    for m in _AMOUNT_PATTERN.finditer(text):
        raw = m.group(0).strip()
        if raw not in seen_amounts:
            seen_amounts.add(raw)
            amounts.append({
                "value": raw,
                "numeric": _parse_amount(m.group(1)),
                "context": _snippet(text, m.start(), m.end()),
                "confidence": 0.8,
            })
    if amounts:
        entities["amounts"] = amounts

    # --- Dates ---
    dates = []
    seen_dates = set()
    for m in _DATE_PATTERN.finditer(text):
        raw = m.group(0).strip()
        if raw not in seen_dates:
            seen_dates.add(raw)
            dates.append({
                "value": raw,
                "context": _snippet(text, m.start(), m.end()),
                "confidence": 0.7,
            })
    if dates:
        entities["dates"] = dates

    # --- Emails ---
    emails = []
    for m in _EMAIL_PATTERN.finditer(text):
        emails.append({
            "value": m.group(0).strip(),
            "context": _snippet(text, m.start(), m.end()),
            "confidence": 0.9,
        })
    if emails:
        entities["emails"] = emails

    # --- Phones ---
    phones = []
    for m in _PHONE_PATTERN.finditer(text):
        phones.append({
            "value": m.group(0).strip(),
            "context": _snippet(text, m.start(), m.end()),
            "confidence": 0.7,
        })
    if phones:
        entities["phones"] = phones

    # --- Reference numbers ---
    refs = []
    for m in _REFERENCE_PATTERN.finditer(text):
        val = m.group(1).strip()
        # Require at least one digit to avoid matching English word fragments
        if re.search(r"\d", val):
            refs.append({
                "value": val,
                "context": _snippet(text, m.start(), m.end()),
                "confidence": 0.8,
            })
    if refs:
        entities["references"] = refs

    # --- Organizations ---
    orgs = []
    for m in _ORG_PATTERN.finditer(text):
        val = m.group(1) or m.group(2)
        if val and val.strip() not in ("", "Select...", "Search..."):
            if not any(o["value"] == val.strip() for o in orgs):
                orgs.append({
                    "value": val.strip(),
                    "context": _snippet(text, m.start(), m.end()),
                    "confidence": 0.6,
                })
    if orgs:
        entities["organizations"] = orgs

    return entities


def _snippet(text: str, start: int, end: int, radius: int = 40) -> str:
    """Extract a text snippet around a match for provenance."""
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    snippet = text[lo:hi].replace("\n", " ")
    if lo > 0:
        snippet = "…" + snippet
    if hi < len(text):
        snippet = snippet + "…"
    return snippet.strip()


def _parse_amount(raw: str) -> float | None:
    """Parse a numeric amount from a matched string."""
    try:
        return float(raw.replace(",", ""))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Store extracted entities as KnowledgeFacts
# ---------------------------------------------------------------------------


def store_document_facts(
    doc_id: int,
    session: Any = None,
    created_by: str = "document_pipeline",
) -> int:
    """Extract entities from a document and store them as KnowledgeFacts.

    Args:
        doc_id: Document ID in the documents table.
        session: DB session (defaults to db.session).
        created_by: Who/what triggered the extraction.

    Returns:
        Number of facts stored.
    """
    s = session or db.session
    doc = s.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        logger.warning("store_document_facts: Document %s not found", doc_id)
        return 0

    text = doc.extracted_text or ""
    if not text.strip():
        logger.info("store_document_facts: Document %s has no extracted text", doc_id)
        return 0

    entities = extract_entities(text)
    if not entities:
        logger.info("store_document_facts: No entities found in document %s", doc_id)
        return 0

    filename = doc.filename or f"doc_{doc_id}"
    classification = doc.classification or "unknown"
    domain = "documents"
    category = f"document.extraction.{classification}"
    provenance = json.dumps({
        "document_id": doc_id,
        "filename": filename,
        "classification": classification,
        "source": "document_extraction_pipeline",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    })

    store = ImmutableKnowledgeStore(session=s)
    fact_count = 0

    entity_type_map = {
        "persons": "person",
        "amounts": "amount",
        "dates": "date",
        "emails": "email",
        "phones": "phone",
        "references": "reference",
        "organizations": "organization",
    }

    for entity_type, items in entities.items():
        mapped_type = entity_type_map.get(entity_type, entity_type)
        for item in items:
            value = item["value"]
            confidence = item.get("confidence", 0.5)
            context = item.get("context", "")

            # Sanitize value for use in fact_key
            sanitized = re.sub(r"[^a-z0-9_]", "_", value.lower())[:60]

            fact_key = f"document.{doc_id}.{mapped_type}.{sanitized}"

            # Build evidence string linking provenance + context
            evidence = (
                f"Extracted from document #{doc_id} ({filename}). "
                f"Context: {context}"
            )

            try:
                store.store(
                    fact_key=fact_key,
                    value=value,  # Will be JSON-serialized if not str
                    domain=domain,
                    category=category,
                    value_type="text",
                    confidence=confidence,
                    evidence=evidence,
                    source="document_extraction",
                    created_by=created_by,
                )
                fact_count += 1
            except Exception as e:
                logger.error(
                    "Failed to store fact %s for document %s: %s",
                    fact_key, doc_id, e,
                )
                db.session.rollback()
                # Re-acquire session after rollback
                s = session or db.session

    logger.info(
        "Stored %d knowledge_facts from document %s (%s)",
        fact_count, doc_id, filename,
    )
    return fact_count


# ---------------------------------------------------------------------------
# Batch backfill
# ---------------------------------------------------------------------------


def backfill_all_documents(session: Any = None) -> dict[str, Any]:
    """Backfill knowledge_facts for all documents that have extracted text.

    Returns:
        dict with keys: total_docs, processed, facts_stored, errors
    """
    s = session or db.session
    docs = s.query(Document).order_by(Document.id).all()

    results = {
        "total_docs": len(docs),
        "processed": 0,
        "facts_stored": 0,
        "errors": [],
        "skipped_no_text": 0,
    }

    for doc in docs:
        text = doc.extracted_text or ""
        if not text.strip():
            results["skipped_no_text"] += 1
            continue

        try:
            count = store_document_facts(doc.id, session=s)
            if count > 0:
                results["processed"] += 1
                results["facts_stored"] += count
        except Exception as e:
            results["errors"].append({
                "doc_id": doc.id,
                "filename": doc.filename,
                "error": str(e),
            })
            s.rollback()
            # Re-acquire session after rollback
            s = session or db.session

    logger.info(
        "Backfill complete: processed=%d/%d, facts_stored=%d, errors=%d",
        results["processed"], results["total_docs"],
        results["facts_stored"], len(results["errors"]),
    )
    return results