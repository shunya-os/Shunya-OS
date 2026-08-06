"""EP-05A — Universal Document Intelligence Runtime.

Documents express Intent. Files express Format.
A document never exists because someone wanted a file.
A document exists because someone wanted something to happen.

Every document participates in Reality, Attention, Cognition, Execution, and Evidence.
"""

import uuid
import logging
import subprocess
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ── Document Types ────────────────────────────────────────────────
# These are metadata differences, not implementation differences.
# One runtime serves all document types.

DOCUMENT_TYPES = {
    "proposal": {"lifecycle": ["Idea", "Draft", "Review", "Negotiation", "Approved", "Executed", "Archived"],
                 "default_purpose": "Win a customer"},
    "contract": {"lifecycle": ["Draft", "Review", "Negotiation", "Signed", "Active", "Expired", "Archived"],
                 "default_purpose": "Formalize an agreement"},
    "invoice":  {"lifecycle": ["Draft", "Sent", "Under Review", "Paid", "Overdue", "Cancelled"],
                 "default_purpose": "Request payment for services"},
    "itinerary": {"lifecycle": ["Planned", "Booked", "In Progress", "Completed", "Archived"],
                  "default_purpose": "Plan a journey"},
    "meeting_notes": {"lifecycle": ["Draft", "Review", "Approved", "Published", "Archived"],
                      "default_purpose": "Record decisions and actions"},
}

DEFAULT_LIFECYCLE = ["Idea", "Draft", "Review", "Approved", "Executed", "Archived"]


# ── Document Living Object ────────────────────────────────────────

@dataclass
class DocumentVersion:
    version_id: str
    content: str
    format: str
    author: str
    created_at: str
    summary: str = ""
    changes: str = ""


@dataclass
class Evidence:
    evidence_id: str
    event_type: str  # approved, signed, converted, exported, etc.
    description: str
    timestamp: str
    actor: str = "system"


@dataclass
class Document:
    """A Document is an intelligent Living Object.
    
    Identity ─ Purpose ─ Intent ─ Relationships ─ Evidence
    Workflow State ─ Version History ─ AI Understanding
    Commitments ─ Reality History ─ Execution History
    
    Content is only one attribute.
    """
    document_id: str
    title: str
    doc_type: str = "proposal"  # proposal, contract, invoice, itinerary, meeting_notes
    format: str = "markdown"
    content: str = ""
    purpose: str = ""
    intent: str = ""
    versions: list[DocumentVersion] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    commitments: list[dict] = field(default_factory=list)
    lifecycle_stage: str = "Idea"
    lifecycle: list[str] = field(default_factory=lambda: DEFAULT_LIFECYCLE.copy())
    ai_summary: str = ""
    ai_risk: str = ""
    ai_recommendation: str = ""
    ocr_text: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "format": self.format,
            "purpose": self.purpose,
            "intent": self.intent,
            "lifecycle_stage": self.lifecycle_stage,
            "lifecycle": self.lifecycle,
            "version_count": len(self.versions),
            "evidence_count": len(self.evidence),
            "relationships": self.relationships,
            "ai_summary": self.ai_summary,
            "ai_risk": self.ai_risk,
            "ai_recommendation": self.ai_recommendation,
            "status": "active" if self.lifecycle_stage not in ("Archived", "Cancelled", "Expired") else "archived",
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def transition(self, target_stage: str, actor: str = "system") -> bool:
        """Transition the document to a new lifecycle stage."""
        if target_stage not in self.lifecycle:
            return False
        current_idx = self.lifecycle.index(self.lifecycle_stage) if self.lifecycle_stage in self.lifecycle else -1
        target_idx = self.lifecycle.index(target_stage)
        if target_idx < current_idx and target_stage != "Archived":
            return False  # Can only go forward (except archive)
        self.lifecycle_stage = target_stage
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.evidence.append(Evidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            event_type=f"transitioned_to_{target_stage.lower()}",
            description=f"Document transitioned to {target_stage}",
            timestamp=self.updated_at,
            actor=actor,
        ))
        return True


# ── Provider Adapter Interface ────────────────────────────────────

class DocumentProvider(ABC):
    @abstractmethod
    def open(self, content: str, source_format: str) -> str: ...
    @abstractmethod
    def save(self, content: str, target_format: str) -> str: ...
    @abstractmethod
    def convert(self, content: str, source_format: str, target_format: str) -> str: ...
    @abstractmethod
    def extract_text(self, content: str, source_format: str) -> str: ...
    @abstractmethod
    def render(self, content: str, source_format: str) -> str: ...


class NativeMarkdownProvider(DocumentProvider):
    def open(self, content: str, source_format: str) -> str:
        return content if source_format == "markdown" else ""
    def save(self, content: str, target_format: str) -> str:
        return content if target_format == "markdown" else ""
    def convert(self, content: str, source_format: str, target_format: str) -> str:
        if source_format == target_format:
            return content
        return f"# Converted from {source_format} to {target_format}\n\n{content}"
    def extract_text(self, content: str, source_format: str) -> str:
        return content
    def render(self, content: str, source_format: str) -> str:
        return content


class PandocProvider(DocumentProvider):
    """Real provider integration using Pandoc (free, open-source, self-hosted).
    
    Supports: markdown, html, docx, pdf, rst, latex, epub, plain, org, etc.
    Provider remains replaceable — workspace code never knows Pandoc exists.
    """
    def convert(self, content: str, source_format: str, target_format: str) -> str:
        try:
            r = subprocess.run(
                ['pandoc', '-f', source_format, '-t', target_format],
                input=content.encode('utf-8'), capture_output=True, timeout=30,
            )
            if r.returncode == 0:
                return r.stdout.decode('utf-8')
            logger.warning(f"Pandoc conversion failed: {r.stderr[:200]}")
            return content
        except FileNotFoundError:
            logger.warning("Pandoc not installed — falling back to native")
            return content
        except Exception as e:
            logger.warning(f"Pandoc error: {e}")
            return content

    def extract_text(self, content: str, source_format: str) -> str:
        return self.convert(content, source_format, "plain")

    def open(self, content: str, source_format: str) -> str:
        return content
    def save(self, content: str, target_format: str) -> str:
        return content
    def render(self, content: str, source_format: str) -> str:
        return self.convert(content, source_format, "html" if source_format == "markdown" else source_format)


# ── Document Intelligence Runtime ─────────────────────────────────

class DocumentRuntime:
    """The single canonical document intelligence runtime for SHUNYA."""

    def __init__(self):
        self._documents: dict[str, Document] = {}
        self._providers: dict[str, DocumentProvider] = {}
        self._register_builtin_providers()

    def _register_builtin_providers(self):
        self.register_provider("markdown", NativeMarkdownProvider())
        self.register_provider("pandoc", PandocProvider())

    def register_provider(self, fmt: str, provider: DocumentProvider):
        self._providers[fmt] = provider

    def get_provider(self, fmt: str) -> Optional[DocumentProvider]:
        return self._providers.get(fmt, self._providers.get("markdown"))

    # ── Document CRUD ──

    def create_document(self, title: str, doc_type: str = "proposal",
                        purpose: str = "", content: str = "",
                        format: str = "markdown") -> Document:
        now = datetime.now(timezone.utc).isoformat()
        type_config = DOCUMENT_TYPES.get(doc_type, {"lifecycle": DEFAULT_LIFECYCLE, "default_purpose": ""})
        doc = Document(
            document_id=f"doc_{uuid.uuid4().hex[:12]}",
            title=title,
            doc_type=doc_type,
            format=format,
            content=content,
            purpose=purpose or type_config.get("default_purpose", ""),
            intent=self._infer_intent(title, doc_type),
            lifecycle=type_config["lifecycle"].copy(),
            lifecycle_stage=type_config["lifecycle"][0],
            created_at=now,
            updated_at=now,
        )
        if content:
            doc.versions.append(DocumentVersion(
                version_id=f"ver_{uuid.uuid4().hex[:12]}",
                content=content, format=format, author="system",
                created_at=now, summary="Initial version",
            ))
        # Auto-discover relationships
        doc.relationships = self._discover_relationships(title, doc_type)
        self._documents[doc.document_id] = doc
        self._emit_reality(doc, "document_created")
        return doc

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._documents.get(doc_id)

    def list_documents(self, doc_type: Optional[str] = None, limit: int = 50) -> list[Document]:
        docs = list(self._documents.values())
        if doc_type:
            docs = [d for d in docs if d.doc_type == doc_type]
        docs.sort(key=lambda d: d.updated_at, reverse=True)
        return docs[:limit]

    # ── Content ──

    def update_content(self, doc_id: str, content: str,
                       author: str = "system") -> Optional[Document]:
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        now = datetime.now(timezone.utc).isoformat()
        doc.versions.append(DocumentVersion(
            version_id=f"ver_{uuid.uuid4().hex[:12]}",
            content=content, format=doc.format, author=author,
            created_at=now,
        ))
        doc.content = content
        doc.updated_at = now
        self._emit_reality(doc, "document_updated")
        return doc

    def convert_format(self, doc_id: str, target_format: str) -> Optional[str]:
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        provider = self.get_provider(doc.format)
        if not provider:
            return None
        result = provider.convert(doc.content, doc.format, target_format)
        if result and result != doc.content:
            doc.evidence.append(Evidence(
                evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                event_type="converted",
                description=f"Converted from {doc.format} to {target_format}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
        return result

    # ── Lifecycle ──

    def transition_document(self, doc_id: str, target_stage: str,
                            actor: str = "system") -> Optional[Document]:
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        if doc.transition(target_stage, actor):
            self._emit_reality(doc, f"document_{target_stage.lower()}")
        return doc

    # ── Evidence ──

    def add_evidence(self, doc_id: str, event_type: str,
                     description: str) -> Optional[Document]:
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        doc.evidence.append(Evidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            description=description,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        self._emit_reality(doc, f"evidence_{event_type}")
        return doc

    # ── Relationships ──

    def _discover_relationships(self, title: str, doc_type: str) -> list[dict]:
        """Auto-discover relationships from document title and type."""
        rels = []
        lower = title.lower()
        # Company detection
        for suffix in [" ltd", " inc", " corp", " llc", " gmbh", " pvt", " limited"]:
            if suffix in lower:
                parts = lower.split(suffix)
                if len(parts) > 1:
                    name = parts[0].strip().title()
                    rels.append({"object_name": name + suffix.upper(), "relationship": "references", "direction": "outbound"})
                    break
        # People detection — simple heuristic
        common_names = ["acme", "globaltech", "acme manufacturing", "acme corp"]
        for name in common_names:
            if name in lower:
                rels.append({"object_name": name.title(), "relationship": "references", "direction": "outbound"})
        return rels

    def add_relationship(self, doc_id: str, object_name: str,
                         relationship: str = "references") -> Optional[Document]:
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        doc.relationships.append({"object_name": object_name, "relationship": relationship, "direction": "outbound"})
        doc.updated_at = datetime.now(timezone.utc).isoformat()
        return doc

    # ── AI Intelligence ──

    def generate_summary(self, doc_id: str) -> str:
        doc = self._documents.get(doc_id)
        if not doc:
            return ""
        preview = doc.content[:300] if doc.content else "Empty"
        doc.ai_summary = (
            f"Document: {doc.title} ({doc.doc_type}). "
            f"Stage: {doc.lifecycle_stage}. Purpose: {doc.purpose}. "
            f"Versions: {len(doc.versions)}. Evidence: {len(doc.evidence)}. "
            f"Relationships: {len(doc.relationships)}. "
            f"Content preview: {preview}"
        )
        return doc.ai_summary

    def analyze_risk(self, doc_id: str) -> str:
        doc = self._documents.get(doc_id)
        if not doc:
            return ""
        risks = []
        if doc.lifecycle_stage in ("Idea", "Draft") and not doc.content:
            risks.append("No content — document is empty")
        if len(doc.versions) > 5 and doc.lifecycle_stage in ("Idea", "Draft"):
            risks.append("Many revisions without advancing lifecycle — may indicate indecision")
        if not doc.relationships:
            risks.append("No related objects — document may lack context")
        if doc.lifecycle_stage in ("Review", "Negotiation") and len(doc.versions) < 2:
            risks.append("In review with only one version — may be premature")
        doc.ai_risk = "; ".join(risks) if risks else "No significant risks detected"
        return doc.ai_risk

    def recommend_action(self, doc_id: str) -> str:
        doc = self._documents.get(doc_id)
        if not doc:
            return ""
        lifecycle = doc.lifecycle
        current = doc.lifecycle_stage
        idx = lifecycle.index(current) if current in lifecycle else -1
        if idx >= 0 and idx + 1 < len(lifecycle):
            doc.ai_recommendation = f"Next action: transition to {lifecycle[idx + 1]}"
        else:
            doc.ai_recommendation = "Document lifecycle complete"
        return doc.ai_recommendation

    # ── OCR ──

    def extract_ocr(self, doc_id: str) -> str:
        doc = self._documents.get(doc_id)
        if not doc:
            return ""
        try:
            r = subprocess.run(['tesseract', 'stdin', 'stdout'],
                               input=doc.content.encode('utf-8'),
                               capture_output=True, timeout=30)
            if r.returncode == 0:
                doc.ocr_text = r.stdout.decode('utf-8')
            else:
                doc.ocr_text = doc.content
        except FileNotFoundError:
            doc.ocr_text = doc.content
        return doc.ocr_text

    # ── Search ──

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for doc in self._documents.values():
            score = 0
            if q in doc.title.lower():
                score += 10
            if q in doc.doc_type.lower():
                score += 8
            if q in doc.purpose.lower():
                score += 6
            if q in doc.content.lower():
                score += 5
            if q in doc.ai_summary.lower():
                score += 3
            if q in doc.ocr_text.lower():
                score += 2
            for v in doc.versions:
                if q in v.content.lower():
                    score += 1
                    break
            if score > 0:
                results.append({"document": doc.to_dict(), "score": score})
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:20]

    # ── Reality ──

    def _infer_intent(self, title: str, doc_type: str) -> str:
        """Infer human intent from the document title and type."""
        intents = {
            "proposal": "Win a customer",
            "contract": "Formalize an agreement",
            "invoice": "Request payment",
            "itinerary": "Plan a journey",
            "meeting_notes": "Record decisions and actions",
        }
        intent = intents.get(doc_type, "Create a document")
        lower = title.lower()
        if "quote" in lower or "estimate" in lower:
            return "Provide a price estimate"
        if "agreement" in lower or "contract" in lower:
            return "Formalize an agreement"
        if "plan" in lower or "strategy" in lower:
            return "Define a plan"
        if "report" in lower:
            return "Produce evidence or analysis"
        return intent

    def _emit_reality(self, doc: Document, event_type: str):
        try:
            from app.reality_engine.engine import get_reality_engine
            engine = get_reality_engine()
            engine.notify({"type": event_type, "identity_id": "system",
                           "document_id": doc.document_id, "title": doc.title,
                           "doc_type": doc.doc_type, "lifecycle_stage": doc.lifecycle_stage})
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────

_RUNTIME_INSTANCE: Optional[DocumentRuntime] = None

def get_document_runtime() -> DocumentRuntime:
    global _RUNTIME_INSTANCE
    if _RUNTIME_INSTANCE is None:
        _RUNTIME_INSTANCE = DocumentRuntime()
    return _RUNTIME_INSTANCE