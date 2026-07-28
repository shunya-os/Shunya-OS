"""
SHUNYA Knowledge Engine — Knowledge Resolution and Synthesis

Resolves facts from observations, synthesizes knowledge, and manages
the knowledge graph built from the Universal Object Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


@dataclass
class KnowledgeFact:
    fact_id: str
    key: str
    value: Any
    source: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    object_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "fact_id": self.fact_id, "key": self.key, "value": self.value,
            "source": self.source, "confidence": self.confidence,
            "created_at": self.created_at.isoformat(), "object_id": self.object_id,
        }


class KnowledgeEngine(Engine):
    """Canonical knowledge engine — manages facts and knowledge resolution."""

    engine_id: str = "knowledge"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._facts: dict[str, KnowledgeFact] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._facts.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={"initialized": self._initialized, "fact_count": len(self._facts)},
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["knowledge.fact.store", "knowledge.fact.recall", "knowledge.search", "knowledge.synthesize"]

    def store(self, key: str, value: Any, source: str = "system", confidence: float = 1.0,
              object_id: Optional[str] = None) -> KnowledgeFact:
        fact = KnowledgeFact(
            fact_id=f"kf-{len(self._facts) + 1}", key=key, value=value,
            source=source, confidence=confidence, object_id=object_id,
        )
        self._facts[fact.fact_id] = fact
        return fact

    def recall(self, key: str) -> list[KnowledgeFact]:
        return [f for f in self._facts.values() if f.key == key]

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [f.to_dict() for f in self._facts.values() if q in f.key.lower() or q in str(f.value).lower()]

    def get(self, fact_id: str) -> Optional[KnowledgeFact]:
        return self._facts.get(fact_id)

    def synthesize(self, fact_ids: list[str]) -> dict:
        results = [self._facts[fid] for fid in fact_ids if fid in self._facts]
        return {"source_count": len(results), "facts": [r.to_dict() for r in results]}