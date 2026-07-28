"""SHUNYA Phase A1 — Universal Space Domain Model.
Phase A1A — Lifecycle, capabilities, AI resident.

Every entity in the Business Graph becomes a Space.
A Space is defined by its identity, not its type.
The canonical structure is identical for every Space.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================


class SpaceStatus(str, Enum):
    """Backward-compatible status enum. Maps to LifecycleState."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SpacePanel(str, Enum):
    CONTEXT = "context"
    RELATIONSHIPS = "relationships"
    TIMELINE = "timeline"
    KNOWLEDGE = "knowledge"
    PLANS = "plans"
    EXECUTION = "execution"
    COMMUNICATIONS = "communications"
    DOCUMENTS = "documents"
    RESPONSIBILITIES = "responsibilities"
    METRICS = "metrics"
    AI_UNDERSTANDING = "ai_understanding"


# =========================================================================
# Value Objects
# =========================================================================


@dataclass
class SpaceIdentity:
    """A Space is defined by its identity — never hardcode type names."""
    space_id: str
    entity_id: str
    entity_type: str
    """Extensible type string. Never hardcode business domains."""
    name: str
    status: SpaceStatus = SpaceStatus.ACTIVE
    aliases: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict:
        return {
            "space_id": self.space_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "status": self.status.value,
            "aliases": self.aliases,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class SpaceContext:
    """Context preservation — last position, collapsed sections, etc."""
    space_id: str
    last_position: str = ""
    """Last scroll position or active panel."""
    collapsed_sections: List[str] = field(default_factory=list)
    recent_conversations: List[str] = field(default_factory=list)
    open_documents: List[str] = field(default_factory=list)
    current_execution: str = ""
    ai_reasoning_context: str = ""
    pending_work: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "space_id": self.space_id,
            "last_position": self.last_position,
            "collapsed_sections": self.collapsed_sections,
            "recent_conversations": self.recent_conversations,
            "open_documents": self.open_documents,
            "current_execution": self.current_execution,
            "ai_reasoning_context": self.ai_reasoning_context,
            "pending_work": self.pending_work,
            "updated_at": self.updated_at,
        }


@dataclass
class SpaceRelationshipRef:
    """A single relationship in the Space's relationship graph."""
    rel_id: str
    target_entity_id: str
    target_entity_name: str
    target_entity_type: str
    rel_type: str
    direction: str = "outgoing"
    """outgoing = source -> target, incoming = target -> source"""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "rel_id": self.rel_id,
            "target_entity_id": self.target_entity_id,
            "target_entity_name": self.target_entity_name,
            "target_entity_type": self.target_entity_type,
            "rel_type": self.rel_type,
            "direction": self.direction,
            "confidence": self.confidence,
        }


@dataclass
class SpaceTimelineEvent:
    """A single event on the Space's unified timeline."""
    event_id: str
    event_type: str
    timestamp: str
    title: str = ""
    description: str = ""
    actor: str = ""
    importance: float = 0.5
    category: str = ""
    """Communication, Decision, Execution, Document, Evidence, Payment,
       Approval, Meeting, Observation, AI Insight"""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "title": self.title,
            "description": self.description,
            "actor": self.actor,
            "importance": self.importance,
            "category": self.category,
        }


@dataclass
class SpaceKnowledgeItem:
    """Native knowledge — documents, emails, messages, notes, etc."""
    item_id: str
    item_type: str
    """document, email, message, note, policy, image, file, research,
       meeting_transcript, ai_summary"""
    title: str
    content_summary: str = ""
    source: str = ""
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "title": self.title,
            "content_summary": self.content_summary,
            "source": self.source,
            "created_at": self.created_at,
        }


@dataclass
class SpacePlanRef:
    """A plan belonging to this Space."""
    plan_id: str
    title: str
    state: str = "proposed"
    priority: str = "normal"
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "state": self.state,
            "priority": self.priority,
            "created_at": self.created_at,
        }


@dataclass
class SpaceExecutionRef:
    """An execution context active in this Space."""
    execution_id: str
    title: str
    status: str = "pending"
    started_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "title": self.title,
            "status": self.status,
            "started_at": self.started_at,
        }


@dataclass
class SpaceCommunicationRef:
    """A communication linked to this Space."""
    comm_id: str
    subject: str
    channel: str = ""
    """email, message, call, meeting"""
    participants: List[str] = field(default_factory=list)
    timestamp: str = ""
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "comm_id": self.comm_id,
            "subject": self.subject,
            "channel": self.channel,
            "participants": self.participants,
            "timestamp": self.timestamp,
            "summary": self.summary,
        }


@dataclass
class SpaceDocumentRef:
    """A document linked to this Space."""
    doc_id: str
    title: str
    doc_type: str = ""
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "created_at": self.created_at,
        }


@dataclass
class SpaceResponsibility:
    """A responsibility assigned in this Space."""
    responsibility_id: str
    actor: str
    description: str
    status: str = "active"
    assigned_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.assigned_at:
            self.assigned_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "responsibility_id": self.responsibility_id,
            "actor": self.actor,
            "description": self.description,
            "status": self.status,
            "assigned_at": self.assigned_at,
        }


@dataclass
class SpaceMetric:
    """A metric tracked for this Space."""
    metric_id: str
    name: str
    value: Any = None
    unit: str = ""
    trend: str = "stable"
    """improving, stable, declining"""
    confidence: float = 1.0
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "trend": self.trend,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
        }


@dataclass
class SpaceAIUnderstanding:
    """SHUNYA's continuous understanding of this Space."""
    summary: str = ""
    goals: List[str] = field(default_factory=list)
    current_plans: List[str] = field(default_factory=list)
    current_communications: List[str] = field(default_factory=list)
    current_responsibilities: List[str] = field(default_factory=list)
    current_risks: List[str] = field(default_factory=list)
    current_opportunities: List[str] = field(default_factory=list)
    current_knowledge: List[str] = field(default_factory=list)
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "goals": self.goals,
            "current_plans": self.current_plans,
            "current_communications": self.current_communications,
            "current_responsibilities": self.current_responsibilities,
            "current_risks": self.current_risks,
            "current_opportunities": self.current_opportunities,
            "current_knowledge": self.current_knowledge,
            "updated_at": self.updated_at,
        }


# =========================================================================
# Universal Space — the primary model
# =========================================================================


@dataclass
class UniversalSpace:
    """The fundamental environment for human-AI collaboration around any object.

    A Space is NOT defined by its type. It is defined by its identity.
    Every Space exposes the same canonical structure.

    Backing runtimes (reused, never duplicated):
        - Business Graph (app.graph_universal)
        - Planning Runtime (app.planning)
        - Organization Runtime (app.organization)
        - Execution Runtime (app.execution)
        - Orchestration Runtime (app.orchestration)
        - Knowledge Runtime (app.knowledge)
        - Intelligence Layer (app.intelligence)
    """
    identity: SpaceIdentity
    context: SpaceContext = field(default_factory=lambda: SpaceContext(space_id=""))
    relationships: List[SpaceRelationshipRef] = field(default_factory=list)
    timeline: List[SpaceTimelineEvent] = field(default_factory=list)
    knowledge: List[SpaceKnowledgeItem] = field(default_factory=list)
    plans: List[SpacePlanRef] = field(default_factory=list)
    executions: List[SpaceExecutionRef] = field(default_factory=list)
    communications: List[SpaceCommunicationRef] = field(default_factory=list)
    documents: List[SpaceDocumentRef] = field(default_factory=list)
    responsibilities: List[SpaceResponsibility] = field(default_factory=list)
    metrics: List[SpaceMetric] = field(default_factory=list)
    ai_understanding: SpaceAIUnderstanding = field(default_factory=SpaceAIUnderstanding)
    parent_space_id: str = ""
    child_space_ids: List[str] = field(default_factory=list)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    """{identity_id: [role, ...]}"""
    commands: List[str] = field(default_factory=lambda: [
        "summarize", "explain", "create_plan", "delegate", "compare",
        "forecast", "generate", "review", "approve", "schedule",
        "analyze", "find_risks", "show_dependencies", "predict_outcome",
    ])
    capabilities: List[str] = field(default_factory=list)
    """Capability names this Space advertises."""
    lifecycle: "SpaceLifecycle" = field(
        default_factory=lambda: __import__(
            "app.space.lifecycle", fromlist=["SpaceLifecycle"]
        ).SpaceLifecycle()
    )
    ai_resident: "AIResidentState" = field(
        default_factory=lambda: __import__(
            "app.space.resident", fromlist=["AIResidentState"]
        ).AIResidentState(space_id="")
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.context.space_id:
            self.context.space_id = self.identity.space_id
        if not self.ai_resident.space_id:
            self.ai_resident.space_id = self.identity.space_id

    @property
    def space_id(self) -> str:
        return self.identity.space_id

    @property
    def entity_id(self) -> str:
        return self.identity.entity_id

    @property
    def entity_type(self) -> str:
        return self.identity.entity_type

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def status(self) -> SpaceStatus:
        return self.identity.status

    def to_dict(self) -> dict:
        return {
            "identity": self.identity.to_dict(),
            "context": self.context.to_dict(),
            "relationships": [r.to_dict() for r in self.relationships],
            "timeline": [e.to_dict() for e in self.timeline],
            "knowledge": [k.to_dict() for k in self.knowledge],
            "plans": [p.to_dict() for p in self.plans],
            "executions": [e.to_dict() for e in self.executions],
            "communications": [c.to_dict() for c in self.communications],
            "documents": [d.to_dict() for d in self.documents],
            "responsibilities": [r.to_dict() for r in self.responsibilities],
            "metrics": [m.to_dict() for m in self.metrics],
            "ai_understanding": self.ai_understanding.to_dict(),
            "parent_space_id": self.parent_space_id,
            "child_space_ids": self.child_space_ids,
            "permissions": self.permissions,
            "commands": self.commands,
            "capabilities": self.capabilities,
            "lifecycle": self.lifecycle.to_dict(),
            "ai_resident": self.ai_resident.to_dict(),
        }

    def to_summary(self) -> dict:
        """Lightweight summary for list views."""
        return {
            "space_id": self.space_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "status": self.identity.status.value,
            "lifecycle_state": self.lifecycle.state.value,
            "relationship_count": len(self.relationships),
            "timeline_count": len(self.timeline),
            "knowledge_count": len(self.knowledge),
            "plan_count": len(self.plans),
            "execution_count": len(self.executions),
            "communication_count": len(self.communications),
            "document_count": len(self.documents),
            "parent_space_id": self.parent_space_id,
            "child_count": len(self.child_space_ids),
            "capabilities": self.capabilities,
            "created_at": self.identity.created_at,
            "updated_at": self.identity.updated_at,
        }