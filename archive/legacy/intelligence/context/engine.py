"""
SHUNYA Context Engine — Context Fusion, Organizational State, and Workspace Awareness

Fuses context from multiple sources to provide a unified understanding
of the current state. Manages attention items and health dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from core.runtime.models import Engine, EngineStatus, HealthLevel, HealthStatus


@dataclass
class ContextFrame:
    context_id: str
    workspace_id: Optional[str] = None
    object_id: Optional[str] = None
    actor_id: Optional[str] = None
    state: dict = field(default_factory=dict)
    attention_items: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Brief:
    organization_id: str
    summary: str
    health_dimensions: dict = field(default_factory=dict)
    attention_count: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ContextEngine(Engine):
    """Canonical context engine for organizational awareness and context fusion."""

    engine_id: str = "context"
    engine_type: str = "intelligence"

    def __init__(self) -> None:
        super().__init__()
        self._frames: dict[str, ContextFrame] = {}
        self._attention_items: list[dict] = []
        self._health_dimensions: dict[str, float] = {}
        self._briefs: dict[str, Brief] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._status = EngineStatus.ACTIVE
        self._initialized = True

    def shutdown(self) -> None:
        self._frames.clear()
        self._attention_items.clear()
        self._health_dimensions.clear()
        self._briefs.clear()
        self._status = EngineStatus.OFFLINE
        self._initialized = False

    def health_check(self) -> HealthStatus:
        return HealthStatus(
            status=HealthLevel.HEALTHY if self._initialized else HealthLevel.UNHEALTHY,
            checks={
                "initialized": self._initialized,
                "frame_count": len(self._frames),
                "attention_count": len(self._attention_items),
            },
        )

    def handle_event(self, event: Any) -> None:
        if not self._initialized:
            return

    def get_capabilities(self) -> List[str]:
        return ["context.fuse", "context.attention", "context.health", "context.brief"]

    def fuse(self, workspace_id: Optional[str] = None, object_id: Optional[str] = None,
             actor_id: Optional[str] = None) -> ContextFrame:
        frame = ContextFrame(
            context_id=f"ctx-{len(self._frames) + 1}",
            workspace_id=workspace_id, object_id=object_id, actor_id=actor_id,
            state={"workspace_id": workspace_id, "health": self._health_dimensions},
            attention_items=self._attention_items[-10:],
        )
        self._frames[frame.context_id] = frame
        return frame

    def add_attention(self, item: dict) -> None:
        item["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._attention_items.append(item)

    def set_health_dimension(self, name: str, score: float) -> None:
        self._health_dimensions[name] = max(0.0, min(1.0, score))

    def generate_brief(self, organization_id: str) -> Brief:
        brief = Brief(
            organization_id=organization_id,
            summary=f"Organization {organization_id} status report",
            health_dimensions=dict(self._health_dimensions),
            attention_count=len(self._attention_items),
        )
        self._briefs[organization_id] = brief
        return brief

    def get_health_dimensions(self) -> dict:
        return dict(self._health_dimensions)

    def get_attention_items(self) -> list[dict]:
        return list(self._attention_items)