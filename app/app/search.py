"""
Shunya — Universal Search (Phase 2)

Single search across all entities: leads, payments, invoices, suppliers,
knowledge facts, observations, learning entries, media files.
"""

from app import db
from sqlalchemy import func, or_


class UniversalSearch:
    """Search across all entities with a single query."""

    def __init__(self, session=None):
        self._session = session or db.session

    def search(self, query: str, limit: int = 10) -> dict:
        """Search everything and return categorized results."""
        q = f"%{query}%"
        results = {}

        # Leads
        from app.models import Lead
        leads = (
            self._session.query(Lead)
            .filter(
                or_(
                    Lead.code.ilike(q), Lead.customer_name.ilike(q),
                    Lead.destination.ilike(q), Lead.phone.ilike(q),
                    Lead.email.ilike(q), Lead.notes.ilike(q),
                )
            )
            .order_by(Lead.created_at.desc())
            .limit(limit)
            .all()
        )
        results["leads"] = [{"id": l.id, "code": l.code, "name": l.customer_name,
                             "destination": l.destination, "status": l.status,
                             "type": "lead"}
                            for l in leads]

        # Payments
        from app.models import Payment
        payments = (
            self._session.query(Payment)
            .filter(
                or_(
                    Payment.method.ilike(q), Payment.ref_number.ilike(q),
                    Payment.notes.ilike(q),
                )
            )
            .order_by(Payment.paid_at.desc())
            .limit(limit)
            .all()
        )
        results["payments"] = [{"id": p.id, "amount": float(p.amount or 0),
                                "method": p.method, "type": p.type, "type_label": "payment"}
                               for p in payments]

        # Invoices
        from app.models import Invoice
        invoices = (
            self._session.query(Invoice)
            .filter(
                or_(
                    Invoice.invoice_number.ilike(q), Invoice.status.ilike(q),
                )
            )
            .order_by(Invoice.raised_at.desc())
            .limit(limit)
            .all()
        )
        results["invoices"] = [{"id": i.id, "number": i.invoice_number,
                                "amount": float(i.grand_total or 0), "status": i.status,
                                "type_label": "invoice"}
                               for i in invoices]

        # Suppliers
        from app.models import Supplier
        suppliers = (
            self._session.query(Supplier)
            .filter(
                or_(
                    Supplier.name.ilike(q), Supplier.category.ilike(q),
                    Supplier.city.ilike(q), Supplier.contact.ilike(q),
                    Supplier.gstin.ilike(q),
                )
            )
            .order_by(Supplier.name)
            .limit(limit)
            .all()
        )
        results["suppliers"] = [{"id": s.id, "name": s.name, "category": s.category,
                                  "city": s.city, "type_label": "supplier"}
                                for s in suppliers]

        # Knowledge facts
        try:
            from app.shunya.knowledge_store import KnowledgeFact
            facts = (
                self._session.query(KnowledgeFact)
                .filter(
                    KnowledgeFact.superseded_at.is_(None),
                    or_(
                        KnowledgeFact.fact_key.ilike(q),
                        KnowledgeFact.value.ilike(q),
                        KnowledgeFact.category.ilike(q),
                    ),
                )
                .order_by(KnowledgeFact.created_at.desc())
                .limit(limit)
                .all()
            )
            results["knowledge"] = [{"id": f.id, "key": f.fact_key, "category": f.category,
                                      "type_label": "knowledge"}
                                    for f in facts]
        except Exception:
            results["knowledge"] = []

        # Media files
        try:
            from app.media import MediaFile
            media = (
                self._session.query(MediaFile)
                .filter(
                    or_(
                        MediaFile.filename.ilike(q),
                        MediaFile.caption.ilike(q),
                    )
                )
                .order_by(MediaFile.created_at.desc())
                .limit(limit)
                .all()
            )
            results["media"] = [{"id": m.id, "filename": m.filename,
                                  "file_type": m.file_type, "type_label": "media"}
                                for m in media]
        except Exception:
            results["media"] = []

        return results

    def search_all(self, query: str, limit: int = 10) -> list[dict]:
        """Flattened search results across all types."""
        results = self.search(query, limit)
        flat = []
        for category, items in results.items():
            for item in items:
                item["category"] = category
                flat.append(item)
        return sorted(flat, key=lambda x: x.get("id", 0), reverse=True)[:limit]