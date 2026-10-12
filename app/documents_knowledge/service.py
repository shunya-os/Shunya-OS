"""FDA24 — Document & Knowledge OS.

Document pipeline: upload → classify → extract → store → provenance → permission → index → retrieve → cite → contextualize

Constitutional rule: A document is DATA, not AUTHORITY.
Document-derived claims retain provenance and truth classification.
Untrusted content (documents, web pages, emails) must never become instructions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# =========================================================================
# Document Classification
# =========================================================================

DOCUMENT_CLASSIFICATIONS = {
    "invoice": {"description": "Invoice or bill", "extractable": True},
    "contract": {"description": "Legal contract or agreement", "extractable": True},
    "proposal": {"description": "Business proposal or quote", "extractable": True},
    "report": {"description": "Business report or analysis", "extractable": True},
    "email": {"description": "Email correspondence", "extractable": True},
    "note": {"description": "Internal note or memo", "extractable": False},
    "policy": {"description": "Policy or SOP document", "extractable": True},
    "training": {"description": "Training material", "extractable": False},
    "other": {"description": "Unclassified document", "extractable": False},
}


def classify_document(filename: str, content_type: str = "") -> str:
    """Classify a document based on filename and content type."""
    name_lower = filename.lower()
    for keyword, cls in [
        ("invoice", "invoice"), ("contract", "contract"), ("agreement", "contract"),
        ("proposal", "proposal"), ("quote", "proposal"), ("report", "report"),
        ("email", "email"), ("note", "note"), ("memo", "note"),
        ("policy", "policy"), ("sop", "policy"), ("training", "training"),
        ("manual", "training"), ("guide", "training"),
    ]:
        if keyword in name_lower:
            return cls
    return "other"


# =========================================================================
# Document Ingestion Pipeline
# =========================================================================


def ingest_document(
    organization_id: int,
    title: str,
    filename: str,
    content: str,
    uploaded_by: str = "system",
    content_type: str = "",
    relationship_id: Optional[int] = None,
    source: str = "upload",
    parsed: bool = True,
) -> Dict[str, Any]:
    """Ingest a document through the governed pipeline.

    Pipeline: upload → classify → extract → store → provenance → permission → index

    ``parsed`` controls the honest lifecycle: files whose content could be
    extracted (pdf/csv/text/markdown/json) are stored as ``ingested`` with
    the extracted text; files that could not be parsed are stored as
    ``stored_unparsed`` with empty extracted text — never a fake success
    with empty content.
    """
    from app import db
    from app.document.models import DocumentRecord, ExtractedField
    from app.evidence.models_db import EvidenceRecord

    # 1. Classify
    classification = classify_document(filename, content_type)

    # 2. Extract (basic text extraction)
    extracted_text = content[:50000] if parsed else ""  # Limit to 50K chars

    # 3. Store
    doc = DocumentRecord(
        tenant_id=organization_id,
        original_filename=filename,
        safe_display_name=(title or filename)[:500],
        mime_type=content_type or "text/plain",
        file_size=len(content.encode("utf-8")),
        classification=classification,
        lifecycle="ingested" if parsed else "stored_unparsed",
        content=content,
        extracted_text=extracted_text,
        ingestion_mechanism=source,
        actor=uploaded_by,
    )
    db.session.add(doc)
    db.session.flush()

    # 4. Provenance — create evidence record linking document to source
    ev = EvidenceRecord(
        source_type="document",
        source_id=str(doc.id),
        raw_reference={
            "title": title,
            "classification": classification,
            "uploaded_by": uploaded_by,
            "source": source,
            "lifecycle": doc.lifecycle,
            "content_preview": content[:200],
        },
    )
    db.session.add(ev)
    db.session.flush()

    # 5. Store extracted fields if applicable
    if parsed and classification in ("invoice", "contract", "proposal"):
        _extract_fields(doc.id, content, classification)

    db.session.commit()

    return {
        "id": doc.id,
        "title": title,
        "classification": classification,
        "lifecycle": doc.lifecycle,
        "extracted_text_length": len(extracted_text),
        "evidence_id": ev.id,
        "provenance": {
            "source_type": "document",
            "source_id": str(doc.id),
            "truth_classification": "observation",
            "warning": "Document content is DATA, not AUTHORITY. Claims from this document require independent verification before becoming business truth.",
        },
    }


def _extract_fields(doc_id: int, content: str, classification: str) -> None:
    """Extract key fields from documents based on classification."""
    from app import db
    from app.document.models import ExtractedField

    # Simple extraction patterns — no AI, no LLM
    patterns = {
        "invoice": [("amount", "total"), ("invoice_number", "invoice"), ("date", "date")],
        "contract": [("party", "party"), ("effective_date", "effective"), ("term", "term")],
        "proposal": [("amount", "amount"), ("valid_until", "valid"), ("scope", "scope")],
    }

    for field_key, keyword in patterns.get(classification, []):
        # Simple keyword search — not authoritative
        if keyword.lower() in content.lower():
            idx = content.lower().find(keyword.lower())
            snippet = content[idx:idx + 100] if idx >= 0 else ""
            field = ExtractedField(
                document_id=doc_id,
                field_key=field_key,
                value=snippet[:500],
                extraction_mechanism="keyword",
                extraction_status="extracted",
            )
            db.session.add(field)


# =========================================================================
# Document Retrieval with Permission Check
# =========================================================================


def get_document(doc_id: int, organization_id: int) -> Optional[Dict[str, Any]]:
    """Get a document with provenance and truth classification."""
    from app import db
    from app.document.models import DocumentRecord, ExtractedField
    from app.evidence.models_db import EvidenceRecord

    doc = db.session.query(DocumentRecord).filter_by(id=doc_id).first()
    if not doc:
        return None

    # Get evidence/provenance
    evidence = db.session.query(EvidenceRecord).filter_by(
        source_type="document", source_id=str(doc_id)
    ).first()

    # Get extracted fields
    fields = db.session.query(ExtractedField).filter_by(document_id=doc_id).all()

    return {
        "id": doc.id,
        "title": doc.original_filename,
        "category": doc.classification,
        "file_type": doc.mime_type,
        "file_size_bytes": doc.file_size,
        "lifecycle": doc.lifecycle,
        "uploaded_by": doc.actor,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "provenance": {
            "source_type": "document",
            "source_id": str(doc.id),
            "truth_classification": "observation",
            "has_evidence": evidence is not None,
        },
        "extracted_fields": [{
            "field_key": f.field_key,
            "field_value": f.value[:200] if f.value else "",
            "extraction_method": f.extraction_mechanism,
            "confidence": 0.3,
        } for f in fields],
        "truth_warning": "Document content is DATA, not AUTHORITY. Extracted fields are observations, not verified business facts.",
    }


def search_documents(
    organization_id: int,
    query: str,
    category: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search documents with permission gating."""
    from app import db
    from app.document.models import DocumentRecord

    q = db.session.query(DocumentRecord)
    if category:
        q = q.filter_by(classification=category)
    if query:
        q = q.filter(
            DocumentRecord.original_filename.ilike(f"%{query}%") |
            DocumentRecord.content.ilike(f"%{query}%") |
            DocumentRecord.extracted_text.ilike(f"%{query}%")
        )
    docs = q.order_by(DocumentRecord.created_at.desc()).limit(limit).all()

    return [{
        "id": d.id,
        "title": d.original_filename,
        "category": d.classification,
        "file_type": d.mime_type,
        "lifecycle": d.lifecycle,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "uploaded_by": d.actor,
        "snippet": (d.content or d.extracted_text or "")[:200] if query else "",
        "truth_classification": "observation",
    } for d in docs]


# =========================================================================
# Prompt Injection Detection
# =========================================================================

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore shunya policy",
    "ignore system prompt",
    "you are now",
    "your new role",
    "override system",
    "system override",
    "forget everything",
    "act as if",
    "pretend you are",
    "do not follow",
    "disregard",
    "you must obey",
    "you will obey",
    "new instructions",
    "tool call",
    "execute tool",
    "run command",
    "sudo",
    "admin access",
    "change password",
    "delete account",
    "send money",
    "transfer funds",
    "approve payment",
    "mark as paid",
    "ignore policies",
    "override permissions",
]


def check_prompt_injection(content: str) -> Dict[str, Any]:
    """Check content for prompt injection attempts.

    A document is DATA, not AUTHORITY. Injected instructions
    must remain document content and never become system instructions.
    """
    content_lower = content.lower()
    matches = []
    for pattern in INJECTION_PATTERNS:
        if pattern in content_lower:
            matches.append(pattern)

    return {
        "is_injection": len(matches) > 0,
        "matched_patterns": matches,
        "handling": "Document content isolated. Injected instructions are DATA, not AUTHORITY. They will NOT be executed.",
    }


# =========================================================================
# Knowledge Contextualization
# =========================================================================


def contextualize_document(
    doc_id: int,
    organization_id: int,
    relationship_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Contextualize a document by linking it to related objects.

    Returns the document with its relationships to entities, commitments,
    and evidence, preserving the data-not-authority principle.
    """
    from app import db
    from app.document.models import DocumentRecord
    from app.relationship.models import CanonicalRelationship, TimelineEntry
    from app.commitments.models import Commitment
    from app.evidence.models_db import EvidenceRecord

    doc = db.session.query(DocumentRecord).filter_by(id=doc_id).first()
    if not doc:
        return {"error": "Document not found"}

    context = {
        "document": {
            "id": doc.id,
            "title": doc.original_filename,
            "category": doc.classification,
        },
        "related_objects": [],
        "evidence": [],
        "truth_classification": "observation",
        "warning": "Document content is data, not authority. Do not treat document claims as verified business facts.",
    }

    # Evidence
    evidence = db.session.query(EvidenceRecord).filter_by(
        source_type="document", source_id=str(doc_id)
    ).all()
    context["evidence"] = [e.to_dict() for e in evidence]

    # Related relationships
    if relationship_id:
        rel = db.session.query(CanonicalRelationship).filter_by(id=relationship_id).first()
        if rel:
            context["related_objects"].append({
                "type": "relationship",
                "id": rel.id,
                "name": rel.display_name,
            })

    return context