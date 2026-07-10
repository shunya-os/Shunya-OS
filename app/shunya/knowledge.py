"""
Knowledge Layer (Shunya)
Destination knowledge, supplier catalog, past itinerary repository.
"""

import json
import os
from datetime import datetime
from typing import Optional


KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge-base.md")


class Destination:
    """Represents knowledge about a travel destination."""
    def __init__(self, name: str, country: str, region: str = ""):
        self.name = name
        self.country = country
        self.region = region
        self.visa_requirements: list[str] = []
        self.best_months: list[str] = []
        self.weather_notes: str = ""
        self.local_taxes: list[dict] = []  # [{"name": "VAT", "rate": 0.15, "notes": ""}]
        self.currency: str = ""
        self.language: str = ""
        self.union_regulations: str = ""
        self.tips: list[str] = []


class KnowledgeLayer:
    """
    Manages the knowledge base — destinations, suppliers, past itineraries.
    Provides search and retrieval for the Reasoning layer.
    """

    def __init__(self, db_session=None):
        self._db = db_session
        self._knowledge_text = self._load_knowledge_base()

    def _load_knowledge_base(self) -> str:
        """Load the knowledge-base markdown file."""
        if os.path.exists(KNOWLEDGE_BASE_PATH):
            with open(KNOWLEDGE_BASE_PATH, "r") as f:
                return f.read()
        return ""

    def get_knowledge_base_text(self) -> str:
        """Return full knowledge base as text for LLM consumption."""
        return self._knowledge_text

    def search_destination(self, query: str) -> Optional[Destination]:
        """
        Search destination knowledge. In Phase 1, this is a simple
        keyword match over the knowledge base. Phase 2 will use pgvector.
        """
        text = self._knowledge_text.lower()
        q = query.lower()

        if q in text:
            dest = Destination(name=query, country="", region="")
            # Extract relevant section from knowledge base
            lines = self._knowledge_text.split("\n")
            capture = False
            section = []
            for line in lines:
                if query.lower() in line.lower() and line.strip().startswith("##"):
                    capture = True
                elif capture and line.strip().startswith("##") and query.lower() not in line.lower():
                    break
                if capture:
                    section.append(line)
            dest.weather_notes = "\n".join(section) if section else ""
            return dest

        return None

    def get_past_itineraries(self, destination: str = "", limit: int = 5) -> list[dict]:
        """Retrieve past itineraries from the database for reference."""
        if not self._db:
            return []

        from app.models import ItineraryRef
        query = self._db.query(ItineraryRef)
        if destination:
            query = query.filter(ItineraryRef.destination.ilike(f"%{destination}%"))
        results = query.order_by(ItineraryRef.created_at.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "guest": r.guest_name,
                "destination": r.destination,
                "dates": f"{r.start_date} to {r.end_date}",
                "pax": r.pax,
                "highlights": r.highlights,
                "file": r.file_path,
            }
            for r in results
        ]

    def get_suppliers_by_destination(self, destination: str) -> list[dict]:
        """Get known suppliers for a destination."""
        if not self._db:
            return []

        from app.models import Supplier
        results = self._db.query(Supplier).filter(
            Supplier.city.ilike(f"%{destination}%")
        ).all()

        return [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "contact": s.contact,
                "city": s.city,
            }
            for s in results
        ]

    def refresh(self):
        """Reload knowledge base from disk."""
        self._knowledge_text = self._load_knowledge_base()