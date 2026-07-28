"""
SHUNYA — Document Service (Phase 7A)
"""
import hashlib
from datetime import datetime
from typing import Optional
from app import db
from app.document.models import (
    DocumentRecord, DocumentSection, ExtractedField, DocumentComparison, ComparisonItem,
    DocumentLifecycle, DocumentClassification, ExtractionStatus, OcrState,
)


class DocumentService:
    def __init__(self, session=None):
        self._session = session or db.session

    def ingest_document(self, tenant_id: Optional[int], original_filename: str,
                         mime_type: str, file_size: int = 0, content: bytes = b"", **kw) -> DocumentRecord:
        content_hash = hashlib.sha256(content).hexdigest()[:64] if content else ""
        doc = DocumentRecord(tenant_id=tenant_id, original_filename=original_filename,
            safe_display_name=original_filename, mime_type=mime_type,
            content_hash=content_hash, file_size=file_size,
            lifecycle=DocumentLifecycle.RECEIVED, **kw)
        self._session.add(doc); self._session.commit()
        return doc

    def get_document(self, doc_id: int, tenant_id: Optional[int] = None) -> Optional[DocumentRecord]:
        doc = self._session.get(DocumentRecord, doc_id)
        if not doc: return None
        if tenant_id is not None and doc.tenant_id != tenant_id: return None
        return doc

    def list_documents(self, tenant_id: Optional[int] = None) -> list[DocumentRecord]:
        q = self._session.query(DocumentRecord)
        if tenant_id: q = q.filter(DocumentRecord.tenant_id == tenant_id)
        return q.order_by(DocumentRecord.created_at.desc()).all()

    def create_section(self, doc_id: int, tenant_id: Optional[int] = None,
                        section_type: str = "text", **kw) -> DocumentSection:
        sec = DocumentSection(tenant_id=tenant_id, document_id=doc_id, section_type=section_type, **kw)
        self._session.add(sec); self._session.commit()
        return sec

    def create_field(self, doc_id: int, field_key: str, value: str,
                      tenant_id: Optional[int] = None, **kw) -> ExtractedField:
        fld = ExtractedField(tenant_id=tenant_id, document_id=doc_id, field_key=field_key, value=value, **kw)
        self._session.add(fld); self._session.commit()
        return fld

    def compare_documents(self, left_id: int, right_id: int,
                           tenant_id: Optional[int] = None) -> dict:
        left = self.get_document(left_id, tenant_id)
        right = self.get_document(right_id, tenant_id)
        if not left or not right:
            return {"success": False, "error": "Document not found"}
        comparison = DocumentComparison(tenant_id=tenant_id, left_document_id=left_id, right_document_id=right_id)
        self._session.add(comparison); self._session.flush()
        items = []
        left_fields = self._session.query(ExtractedField).filter_by(document_id=left_id, status="active").all()
        right_fields = self._session.query(ExtractedField).filter_by(document_id=right_id, status="active").all()
        right_by_key = {f.field_key: f for f in right_fields}
        for lf in left_fields:
            rf = right_by_key.pop(lf.field_key, None)
            if not rf:
                result = "left_only"
            elif lf.value == rf.value:
                result = "equal"
            else:
                result = "different"
            ci = ComparisonItem(tenant_id=tenant_id, comparison_id=comparison.id,
                field_key=lf.field_key, left_value=lf.value,
                right_value=rf.value if rf else "",
                result=result, location_left=lf.location, location_right=rf.location if rf else "")
            self._session.add(ci); items.append(ci)
        for rf in right_by_key.values():
            ci = ComparisonItem(tenant_id=tenant_id, comparison_id=comparison.id,
                field_key=rf.field_key, left_value="", right_value=rf.value,
                result="right_only", location_right=rf.location)
            self._session.add(ci); items.append(ci)
        comparison.comparison_state = "complete"
        self._session.commit()
        return {"success": True, "comparison_id": comparison.id, "items": len(items)}

    def revoke_document(self, doc_id: int, tenant_id: Optional[int] = None) -> dict:
        doc = self.get_document(doc_id, tenant_id)
        if not doc: return {"success": False, "error": "Not found"}
        doc.lifecycle = DocumentLifecycle.REVOKED; self._session.commit()
        return {"success": True, "lifecycle": DocumentLifecycle.REVOKED}