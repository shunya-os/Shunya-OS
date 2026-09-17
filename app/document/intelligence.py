"""SHUNYA — Document Intelligence service.

Ties document identification (classification) and entity extraction into a
single persisted result stored ON the document record, so the intelligence is
durable and re-readable without recomputation.

Result shape (stored in Document.structured_data as JSON):
    {
      "intelligence": {
        "classification": "invoice",
        "confidence": 0.82,
        "reason": "...",
        "signals": ["invoice no", "amount due"],
        "entities": {"amounts": [...], "dates": [...], ...},
        "entity_count": 7,
        "analysed_at": "2026-09-17T...Z",
        "engine": "document_intelligence/1"
      }
    }
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.document.classification import classify_document
from app.document.extraction_pipeline import extract_entities

logger = logging.getLogger(__name__)

ENGINE_VERSION = "document_intelligence/1"


def analyse_document(doc: Any, persist: bool = True) -> dict[str, Any]:
    """Classify + extract entities for a Document, optionally persisting.

    Args:
        doc: a `Document` model instance (must have extracted_text/filename).
        persist: when True, write classification + structured_data back to the
            record (the caller owns the commit).

    Returns:
        The intelligence dict (also persisted under structured_data).
    """
    text = doc.extracted_text or ""
    result = classify_document(text, filename=doc.filename or "", file_type=doc.file_type or "")

    entities: dict[str, list] = {}
    try:
        entities = extract_entities(text) if text.strip() else {}
    except Exception as e:  # never let extraction failure lose the classification
        logger.warning("Entity extraction failed for document %s: %s", getattr(doc, "id", "?"), e)

    entity_count = sum(len(v) for v in entities.values())

    intelligence = {
        "classification": result["classification"],
        "confidence": result["confidence"],
        "reason": result["reason"],
        "signals": result["signals"],
        "entities": entities,
        "entity_count": entity_count,
        "analysed_at": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE_VERSION,
    }

    if persist:
        doc.classification = result["classification"]
        try:
            existing: dict = {}
            if doc.structured_data:
                existing = json.loads(doc.structured_data) or {}
                if not isinstance(existing, dict):
                    existing = {}
            existing["intelligence"] = intelligence
            doc.structured_data = json.dumps(existing)
        except (json.JSONDecodeError, TypeError):
            doc.structured_data = json.dumps({"intelligence": intelligence})

    return intelligence


def read_intelligence(doc: Any) -> dict[str, Any] | None:
    """Return the persisted intelligence for a document, or None if not analysed."""
    try:
        if doc.structured_data:
            data = json.loads(doc.structured_data) or {}
            if isinstance(data, dict) and isinstance(data.get("intelligence"), dict):
                return data["intelligence"]
    except (json.JSONDecodeError, TypeError):
        pass
    return None
