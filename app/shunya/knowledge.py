"""
Shunya — Knowledge Layer (Unit 4, v2)

Loads destination knowledge base, supplier catalog, past itineraries.
Provides structured retrieval for the Reasoning layer.
Phase 2: upgrade to pgvector semantic search.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional

KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge-base.md")


@dataclass
class Destination:
    name: str
    country: str = ""
    region: str = ""
    visa_info: str = ""
    best_months: list[str] = field(default_factory=list)
    weather_notes: str = ""
    currency: str = ""
    currency_note: str = ""
    local_taxes: list[dict] = field(default_factory=list)
    wedding_requirements: str = ""
    transport_notes: str = ""
    transport_cost_range: str = ""
    top_venues: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    raw_section: str = ""


class KnowledgeLayer:
    """
    Manages knowledge base — destinations, suppliers, past itineraries.
    """

    DESTINATIONS = {}  # populated lazily

    def __init__(self, db_session=None):
        self._db = db_session
        self._knowledge_text = self._load_knowledge_base()
        if not KnowledgeLayer.DESTINATIONS:
            KnowledgeLayer.DESTINATIONS = self._parse_knowledge_base()

    def _load_knowledge_base(self) -> str:
        if os.path.exists(KNOWLEDGE_BASE_PATH):
            with open(KNOWLEDGE_BASE_PATH, "r") as f:
                return f.read()
        return ""

    def _parse_knowledge_base(self) -> dict[str, Destination]:
        """Parse the markdown KB into structured Destination objects."""
        if not self._knowledge_text:
            return {}

        dests = {}
        # Split by ## headings
        sections = re.split(r"\n## ", self._knowledge_text)
        for section in sections:
            if not section.strip():
                continue
            lines = section.strip().split("\n")
            title = lines[0].strip().rstrip("#").strip()
            body = "\n".join(lines[1:])
            d = Destination(name=title, raw_section=body)

            for line in lines[1:]:
                lower = line.lower().strip()

                if lower.startswith("### visa"):
                    d.visa_info = _extract_body(lines, lines.index(line))
                elif lower.startswith("### best time"):
                    d.best_months = _extract_body(lines, lines.index(line)).strip().split(", ")
                    d.weather_notes = _extract_body(lines, lines.index(line))
                elif lower.startswith("### currency"):
                    d.currency = _extract_first_line(line, lines, lines.index(line))
                    d.currency_note = _extract_body(lines, lines.index(line))
                elif lower.startswith("### local taxes"):
                    d.local_taxes = _parse_taxes(_extract_body(lines, lines.index(line)))
                elif lower.startswith("### wedding requirements"):
                    d.wedding_requirements = _extract_body(lines, lines.index(line))
                elif lower.startswith("### transport"):
                    d.transport_notes = _extract_body(lines, lines.index(line))
                elif lower.startswith("### top venues"):
                    d.top_venues = _parse_bullets(_extract_body(lines, lines.index(line)))

            # Infer country from context
            for kw, country in [("sri lanka", "Sri Lanka"), ("bali", "Indonesia"),
                                ("maldives", "Maldives"), ("thailand", "Thailand"),
                                ("india", "India")]:
                if kw in title.lower():
                    d.country = country
                    break

            dests[title.lower()] = d

        return dests

    def get_knowledge_base_text(self) -> str:
        return self._knowledge_text

    def search_destination(self, query: str) -> Optional[Destination]:
        """Find a destination by name or alias."""
        q = query.lower().strip()
        # Direct match
        if q in KnowledgeLayer.DESTINATIONS:
            return KnowledgeLayer.DESTINATIONS[q]

        # Partial match
        for key, dest in KnowledgeLayer.DESTINATIONS.items():
            if q in key or key in q:
                return dest

        # Country-level match
        for key, dest in KnowledgeLayer.DESTINATIONS.items():
            if dest.country.lower() in q or q in dest.country.lower():
                return dest

        return None

    def list_destinations(self) -> list[str]:
        return sorted(set(d.name for d in KnowledgeLayer.DESTINATIONS.values()))

    def get_wedding_requirements(self, destination: str) -> str:
        dest = self.search_destination(destination)
        if dest and dest.wedding_requirements:
            return dest.wedding_requirements
        return "General requirements: valid passports, birth certificates, marital status affidavit."

    def get_past_itineraries(self, destination: str = "", limit: int = 5) -> list[dict]:
        if not self._db:
            return []
        from app.models import ItineraryRef
        query = self._db.query(ItineraryRef)
        if destination:
            query = query.filter(ItineraryRef.destination.ilike(f"%{destination}%"))
        results = query.order_by(ItineraryRef.created_at.desc()).limit(limit).all()
        return [r.to_dict() for r in results]

    def get_suppliers_by_category(self, category: str = "", destination: str = "") -> list[dict]:
        if not self._db:
            return []
        from app.models import Supplier
        query = self._db.query(Supplier)
        if category:
            query = query.filter(Supplier.category.ilike(f"%{category}%"))
        if destination:
            query = query.filter(Supplier.city.ilike(f"%{destination}%"))
        results = query.order_by(Supplier.name).limit(20).all()
        return [s.to_dict() for s in results]

    def refresh(self):
        self._knowledge_text = self._load_knowledge_base()
        KnowledgeLayer.DESTINATIONS = self._parse_knowledge_base()


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------

def _extract_body(lines: list[str], start_idx: int) -> str:
    body = []
    for line in lines[start_idx + 1:]:
        if line.startswith("### ") or line.startswith("---"):
            break
        if line.strip():
            body.append(line.rstrip())
    return "\n".join(body) if any(l.lstrip().startswith("-") for l in body) else " ".join(body).strip()


def _extract_first_line(current_line: str, lines: list[str], idx: int) -> str:
    return current_line.replace("###", "").strip()


def _parse_taxes(text: str) -> list[dict]:
    taxes = []
    for line in text.split(". "):
        m = re.match(r"([A-Za-z\s]+):\s*(\d+)%", line)
        if m:
            taxes.append({"name": m.group(1).strip(), "rate": int(m.group(2)) / 100})
    return taxes


def _parse_bullets(text: str) -> list[str]:
    return [line.strip("- ").strip() for line in text.split("\n") if line.strip().startswith("-")]