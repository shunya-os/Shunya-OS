"""
SHUNYA LX-02 — Canonical Reality Engine

The Reality Engine is the single source from which the interface derives.
It composes existing runtime modules (events, attention, objects, execution,
awareness, graph) into a unified, authoritative reality stream.

Key principles:
- Reality Engine computes truth. Runtimes execute behaviour.
- The frontend never knows the transport (polling, SSE, WebSocket, local event bus, replay, offline cache).
- Every meaningful change becomes a Reality Event.
- Attention determines what deserves rendering.
- Projections allow different workspaces to see different slices of the same reality.

Architecture:
    RealityEngine
        │
        ├── EventCollector (pulls from events, execution, objects, awareness, graph)
        ├── AttentionScorer (uses Cortex attention engine)
        ├── RelationshipResolver (uses Universal Graph)
        └── ProjectionBuilder (workspace-specific views)
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from flask import current_app

DEMO_IDENTITY = "sid_demo_tenant"

from app import db
from app.cortex.attention import (
    AttentionEngine, AttentionItem, compute_priority,
    AttentionStatus, ATTENTION_WEIGHTS, get_engine as get_attention_engine,
)
from app.cortex.state import OrganizationState, get_synthesizer
from app.cortex.brief import project_brief
from app.events.routes import _get_delta_objects
from app.execution.models import Outcome
from app.execution.runtime import OutcomeRuntime
from app.graph_universal.entity import get_store as get_entity_store
from app.graph_universal.relationship import get_store as get_rel_store
from app.graph_universal.traversal import GraphQueryEngine
from app.intelligence.observation import get_store as get_obs_store
from app.intelligence.insight import get_compiler
from app.awareness.engine import get_awareness_engine
from app.objects.legacy_models import ShunyaObject, Workspace


# ═════════════════════════════════════════════════════════════════════
# Types
# ═════════════════════════════════════════════════════════════════════


class RealityEventType(str, Enum):
    OBJECT_CREATED = "object_created"
    OBJECT_UPDATED = "object_updated"
    OBJECT_EVOLVED = "object_evolved"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    OUTCOME_ACHIEVED = "outcome_achieved"
    OUTCOME_REJECTED = "outcome_rejected"
    COMMITMENT_DUE = "commitment_due"
    RELATIONSHIP_ADDED = "relationship_added"
    OBSERVATION_ACTIVE = "observation_active"
    INSIGHT_GENERATED = "insight_generated"
    EXTERNAL_SIGNAL = "external_signal"
    USER_ACTION = "user_action"
    ATTENTION_SHIFT = "attention_shift"
    SYSTEM_EVENT = "system_event"


@dataclass
class RealityEvent:
    """A single change in reality.

    Every meaningful business change becomes a RealityEvent.
    """
    event_id: str
    type: RealityEventType
    title: str
    description: str
    timestamp: str
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    object_name: Optional[str] = None
    actor: Optional[str] = None
    importance: str = "normal"  # critical | high | normal | low
    confidence: float = 0.5
    source: str = "reality_engine"
    payload: dict = field(default_factory=dict)
    relationships: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "type": self.type.value if isinstance(self.type, RealityEventType) else self.type,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "actor": self.actor,
            "importance": self.importance,
            "confidence": self.confidence,
            "source": self.source,
            "payload": self.payload,
            "relationships": self.relationships,
        }


@dataclass
class RealitySnapshot:
    """A point-in-time snapshot of the full business reality.

    This is what the frontend subscribes to — not individual API responses.
    """
    snapshot_id: str
    timestamp: str
    events: list[RealityEvent]
    attention_queue: list[dict]
    living_objects: list[dict]
    active_executions: list[dict]
    recent_outcomes: list[dict]
    organization_summary: dict
    cognition: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "events": [e.to_dict() for e in self.events],
            "attention_queue": self.attention_queue,
            "living_objects": self.living_objects,
            "active_executions": self.active_executions,
            "recent_outcomes": self.recent_outcomes,
            "organization_summary": self.organization_summary,
            "cognition": self.cognition,
        }


@dataclass
class RealityProjection:
    """A workspace-specific projection of the canonical reality.

    Different workspaces (Founder, Finance, Travel) get different projections
    of the same underlying reality. The underlying reality is identical — only
    the projection changes.
    """
    projection_id: str
    workspace_type: str  # 'founder' | 'finance' | 'travel' | 'business' | etc.
    workspace_id: str
    timestamp: str
    title: str
    briefing: dict
    attention_items: list[dict]
    objects: list[dict]
    events: list[RealityEvent]

    def to_dict(self) -> dict:
        return {
            "projection_id": self.projection_id,
            "workspace_type": self.workspace_type,
            "workspace_id": self.workspace_id,
            "timestamp": self.timestamp,
            "title": self.title,
            "briefing": self.briefing,
            "attention_items": self.attention_items,
            "objects": self.objects,
            "events": [e.to_dict() for e in self.events],
        }


# ═════════════════════════════════════════════════════════════════════
# Event Collector — pulls from every runtime
# ═════════════════════════════════════════════════════════════════════


class EventCollector:
    """Collects reality events from all runtime modules.

    Transport-agnostic. The collector is called on every reality build
    (whether polled or SSE-pushed) so the frontend never knows.
    """

    def __init__(self):
        self._graph_engine = GraphQueryEngine()

    def collect(self, identity_id: str, since: Optional[datetime] = None) -> list[RealityEvent]:
        """Collect all reality events since the given timestamp."""
        events: list[RealityEvent] = []
        now = datetime.now(timezone.utc)

        # 1. Object delta events
        try:
            created, updated = _get_delta_objects(since or datetime.min)
            for row in created:
                events.append(RealityEvent(
                    event_id=f"evt_obj_create_{row.id}",
                    type=RealityEventType.OBJECT_CREATED,
                    title=f"{row.name} created",
                    description=f"New {row.object_type} created",
                    timestamp=row.created_at.isoformat() if row.created_at else now.isoformat(),
                    object_type=row.object_type,
                    object_id=row.object_id,
                    object_name=row.name,
                    confidence=1.0,
                    source="objects",
                ))
            for row in updated:
                events.append(RealityEvent(
                    event_id=f"evt_obj_update_{row.id}",
                    type=RealityEventType.OBJECT_UPDATED,
                    title=f"{row.name} updated",
                    description=f"{row.object_type} record changed",
                    timestamp=row.updated_at.isoformat() if row.updated_at else now.isoformat(),
                    object_type=row.object_type,
                    object_id=row.object_id,
                    object_name=row.name,
                    confidence=0.9,
                    source="objects",
                ))
        except Exception:
            pass  # Collector is resilient

        # 2. Execution outcome events
        try:
            outcomes = Outcome.query.filter(
                Outcome.created_at > (since or datetime.min)
            ).order_by(Outcome.created_at.desc()).limit(20).all()
            for o in outcomes:
                ev_type = (
                    RealityEventType.EXECUTION_COMPLETED if o.stage == "completed"
                    else RealityEventType.EXECUTION_FAILED if o.stage == "failed"
                    else RealityEventType.EXECUTION_STARTED if o.stage in ("executing", "queued")
                    else RealityEventType.OUTCOME_ACHIEVED
                )
                events.append(RealityEvent(
                    event_id=f"evt_outcome_{o.outcome_id}",
                    type=ev_type,
                    title=f"Outcome: {o.intention[:60]}",
                    description=f"Stage: {o.stage} — {o.progress or ''}",
                    timestamp=o.created_at.isoformat() if o.created_at else now.isoformat(),
                    object_type="outcome",
                    object_id=o.outcome_id,
                    object_name=o.intention[:60],
                    actor=o.identity_id,
                    importance="high" if o.stage == "failed" else "normal",
                    confidence=0.9,
                    source="execution",
                    payload={"stage": o.stage, "progress": o.progress or ""},
                ))
        except Exception:
            pass

        # 3. Active observations
        try:
            obs_store = get_obs_store()
            for obs in obs_store._observations.values():
                if obs.status.value == "active":
                    events.append(RealityEvent(
                        event_id=f"evt_obs_{obs.observation_id}",
                        type=RealityEventType.OBSERVATION_ACTIVE,
                        title=f"Observation: {obs.label}",
                        description=obs.description[:200],
                        timestamp=obs.created_at.isoformat() if obs.created_at else now.isoformat(),
                        confidence=obs.confidence,
                        importance="high" if obs.confidence >= 0.8 else "normal",
                        source="awareness",
                        payload={"confidence": obs.confidence, "age_hours": getattr(obs, 'age_hours', 0)},
                    ))
        except Exception:
            pass

        # 4. Insights
        try:
            compiler = get_compiler()
            insights = compiler.compile_all()
            for ins in insights:
                events.append(RealityEvent(
                    event_id=f"evt_insight_{ins.insight_id}",
                    type=RealityEventType.INSIGHT_GENERATED,
                    title=f"Insight: {ins.label}",
                    description=ins.detail[:200],
                    timestamp=ins.created_at.isoformat() if ins.created_at else now.isoformat(),
                    confidence=ins.confidence,
                    importance="normal",
                    source="intelligence",
                    payload={"confidence": ins.confidence},
                ))
        except Exception:
            pass

        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events


# ═════════════════════════════════════════════════════════════════════
# Attention Scorer
# ═════════════════════════════════════════════════════════════════════


class AttentionScorer:
    """Wraps the Cortex Attention Engine for Reality Engine use.

    Computes what deserves the founder's attention right now based on:
    urgency, opportunity, confidence, execution dependency,
    relationship importance, founder workload, business impact.
    """

    def __init__(self):
        self._attention = get_attention_engine()

    def score(self, identity_id: str, limit: int = 10) -> list[dict]:
        """Get the scored attention queue with full signal details."""
        queue = self._attention.get_attention_queue(limit=limit)
        return [item.to_dict() for item in queue]

    def add_event_to_attention(self, event: RealityEvent) -> None:
        """Add a reality event to the attention engine for scoring."""
        if not event.object_id:
            return

        impact_map = {"critical": 0.9, "high": 0.7, "normal": 0.5, "low": 0.3}
        item = AttentionItem(
            item_id=f"attn_re_{event.event_id}",
            label=event.title,
            description=event.description[:200],
            source_type=event.type.value if isinstance(event.type, RealityEventType) else event.type,
            source_id=event.object_id or event.event_id,
            impact=impact_map.get(event.importance, 0.5),
            urgency=0.8 if event.importance == "critical" else (0.6 if event.importance == "high" else 0.4),
            evidence_confidence=event.confidence,
            opportunity_window=0.5,
            learning_confidence=0.5,
            organizational_reach=0.3,
        )
        self._attention.add_item(item)
        self._attention.reorder()

    @property
    def engine(self) -> AttentionEngine:
        return self._attention


# ═════════════════════════════════════════════════════════════════════
# Relationship Resolver
# ═════════════════════════════════════════════════════════════════════


class RelationshipResolver:
    """Resolves relationships for any entity using the Universal Graph."""

    def __init__(self):
        self._graph = GraphQueryEngine()
        self._rel_store = get_rel_store()
        self._entity_store = get_entity_store()

    def resolve(self, object_id: str, object_type: str, max_depth: int = 2) -> list[dict]:
        """Get all relationships for an entity."""
        # Try Universal Graph first
        try:
            graph_rels = self._graph.neighbors(object_id, max_depth=max_depth)
            if graph_rels:
                return graph_rels
        except Exception:
            pass

        # Fallback: use the relationship store directly
        try:
            rels = self._rel_store.get_for_entity(object_id)
            return [
                {
                    "rel_id": r.rel_id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.rel_type,
                    "confidence": r.confidence,
                }
                for r in rels
            ]
        except Exception:
            return []


# ═════════════════════════════════════════════════════════════════════
# Reality Engine — Main Class
# ═════════════════════════════════════════════════════════════════════


class RealityEngine:
    """The Canonical Reality Engine.

    Composes all runtime modules into a unified view of reality.
    The frontend subscribes to this engine — never to individual APIs.

    Usage:
        engine = get_reality_engine()
        snapshot = engine.build_snapshot(identity_id="sid_xxx")
        projection = engine.build_projection(workspace_type="founder", ...)
    """

    def __init__(self):
        self._event_collector = EventCollector()
        self._attention_scorer = AttentionScorer()
        self._relationship_resolver = RelationshipResolver()
        self._rel_store = get_rel_store()
        self._entity_store = get_entity_store()
        self._last_event_check: dict[str, datetime] = {}

    # ── Public Orchestration Interface (EP-02-R2) ──

    def notify(self, notification: dict) -> None:
        """Receive a typed notification from orchestration runtimes.
        
        The Reality Runtime decides what to do with each notification.
        This is the single public interface — new notification types
        do not require new methods.
        
        Supported notification types:
          - object_created: { type, object_id, object_type, object_name, identity_id }
          - object_updated: { type, object_id, ... }
          - object_deleted: { type, object_id, ... }
          - relationship_created: { type, source_id, target_id, ... }
          - commitment_completed: { type, commitment_id, ... }
          - execution_started: { type, execution_id, ... }
          - execution_failed: { type, execution_id, error, ... }
        """
        notif_type = notification.get("type", "")
        identity_id = notification.get("identity_id", "system")
        
        if notif_type == "object_created":
            # Touch the event collector to prime the next snapshot
            self._event_collector.collect(identity_id)
        elif notif_type == "object_updated":
            self._event_collector.collect(identity_id)
        elif notif_type == "object_deleted":
            self._event_collector.collect(identity_id)
        # Future notification types handled here without new methods
        # Unknown notification types are silently ignored (extensible by design)

    def build_snapshot(self, identity_id: str) -> RealitySnapshot:
        """Build a complete reality snapshot for the given identity.

        Returns everything the frontend needs in a single response.
        """
        # Demonstration Tenant — returns demo data through the same pipeline
        if identity_id == DEMO_IDENTITY:
            return self._build_demo_snapshot()
        
        now = datetime.now(timezone.utc)
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"

        # Determine last check time (per-identity)
        since = self._last_event_check.get(identity_id)
        self._last_event_check[identity_id] = now

        # Collect events
        events = self._event_collector.collect(identity_id, since=since)
        for event in events:
            self._attention_scorer.add_event_to_attention(event)

        # Build attention queue
        attention_queue = self._attention_scorer.score(identity_id, limit=10)

        # Build living objects from object registry
        living_objects = self._build_living_objects(identity_id)

        # Active executions
        active_executions = self._build_active_executions(identity_id)

        # Recent outcomes
        recent_outcomes = self._build_recent_outcomes(identity_id)

        # Organization summary
        org_summary = self._build_org_summary(identity_id)

        # AI cognition
        cognition = self._build_cognition(identity_id)

        return RealitySnapshot(
            snapshot_id=snapshot_id,
            timestamp=now.isoformat(),
            events=events[:30],  # Limit to most recent 30
            attention_queue=attention_queue,
            living_objects=living_objects,
            active_executions=active_executions,
            recent_outcomes=recent_outcomes,
            organization_summary=org_summary,
            cognition=cognition,
        )

    def build_projection(
        self,
        workspace_type: str,
        workspace_id: str,
        identity_id: str,
    ) -> RealityProjection:
        """Build a workspace-specific projection of reality.

        The underlying reality is identical — only the projection changes.
        Different workspaces (founder, finance, travel) see different slices.
        """
        now = datetime.now(timezone.utc)
        snapshot = self.build_snapshot(identity_id)

        # Filter events by workspace relevance
        workspace_events = self._filter_events_for_workspace(snapshot.events, workspace_type)

        # Filter objects by workspace type
        workspace_objects = self._filter_objects_for_workspace(snapshot.living_objects, workspace_type)

        # Build workspace-specific briefing
        briefing = self._build_workspace_briefing(workspace_type, snapshot)

        title_map = {
            "founder": "Executive Reality",
            "finance": "Financial Reality",
            "travel": "Travel Reality",
            "business": "Business Reality",
            "personal": "Personal Reality",
            "studio": "Studio Reality",
        }

        return RealityProjection(
            projection_id=f"proj_{uuid.uuid4().hex[:12]}",
            workspace_type=workspace_type,
            workspace_id=workspace_id,
            timestamp=now.isoformat(),
            title=title_map.get(workspace_type, f"{workspace_type.title()} Reality"),
            briefing=briefing,
            attention_items=snapshot.attention_queue,
            objects=workspace_objects,
            events=workspace_events,
        )

    def _build_living_objects(self, identity_id: str) -> list[dict]:
        """Build living object representations from the object registry.

        Each object is enriched with:
        - Business-meaningful stages (not DB statuses)
        - Relationship stories that explain why they exist
        - Time narratives (human-readable business time)
        - Concrete recommendations with reasoning
        """
        objects = []
        try:
            rows = db.session.execute(
                "SELECT object_id, object_type, name, status, created_at, updated_at, data "
                "FROM sh_objects WHERE is_deleted = false "
                "ORDER BY updated_at DESC LIMIT 50"
            ).fetchall()

            # Build per-type aggregator
            type_buckets: dict[str, list[dict]] = {}
            for row in rows:
                obj_type = row.object_type
                if obj_type not in type_buckets:
                    type_buckets[obj_type] = []
                type_buckets[obj_type].append({
                    "object_id": row.object_id,
                    "object_type": row.object_type,
                    "name": row.name or f"{row.object_type} {row.object_id}",
                    "status": row.status or "active",
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "data": row.data or {},
                })

            for obj_type, records in type_buckets.items():
                # Derive business stage from status + type
                business_stage = self._derive_business_stage(obj_type, records[0]["status"])
                stage_history = self._build_stage_history(obj_type, records)

                # Build relationship story
                relationships = self._build_relationship_story(obj_type, records)

                # Build time narrative
                time_narrative = self._build_time_narrative(records)

                # Build recommendation with reasoning
                recommendation = self._build_object_recommendation(
                    obj_type, records[0]["status"], records
                )

                objects.append({
                    "id": f"obj_{obj_type}",
                    "object_id": records[0]["object_id"],
                    "object_type": obj_type,
                    "name": records[0]["name"],
                    "count": len(records),
                    "current_stage": business_stage,
                    "stage_history": stage_history,
                    "stage_pipeline": self._get_stage_pipeline(obj_type),
                    "summary": f"{len(records)} record(s) — {business_stage}",
                    "relationships": relationships,
                    "time_narrative": time_narrative,
                    "recommendation": recommendation,
                    "next_action": {
                        "label": recommendation["action_label"],
                        "description": recommendation["reasoning"],
                        "action_type": recommendation.get("action_type", "outcome"),
                        "confidence": recommendation.get("confidence", 0.8),
                        "is_primary": True,
                    },
                })
        except Exception as exc:
            current_app.logger.debug("Living objects query failed: %s", exc)
        return objects

    def _derive_business_stage(self, obj_type: str, status: str) -> str:
        """Map object type + DB status to a business-meaningful stage name."""
        stage_map = {
            "lead": {"new": "Inquiry", "active": "Qualified", "proposal": "Proposal Sent",
                     "negotiation": "Negotiating", "won": "Converted", "lost": "Closed"},
            "customer": {"active": "Active", "inactive": "Dormant", "churned": "Churned",
                         "vip": "VIP Engagement"},
            "proposal": {"draft": "Drafting", "sent": "Shared", "viewed": "Viewed",
                         "discussed": "Under Discussion", "approved": "Approved",
                         "rejected": "Not Accepted", "converted": "Converted"},
            "invoice": {"draft": "Drafting", "sent": "Sent", "viewed": "Viewed",
                        "paid": "Paid", "overdue": "Overdue", "cancelled": "Cancelled"},
            "task": {"pending": "Queued", "in_progress": "Working", "completed": "Done",
                     "blocked": "Blocked", "cancelled": "Cancelled"},
            "conversation": {"active": "Active", "waiting": "Awaiting Reply",
                             "resolved": "Resolved", "archived": "Archived"},
            "project": {"planning": "Planning", "active": "Executing",
                        "on_hold": "On Hold", "completed": "Delivered", "cancelled": "Cancelled"},
        }
        mapping = stage_map.get(obj_type, {})
        return mapping.get(status, status.replace("_", " ").title())

    def _get_stage_pipeline(self, obj_type: str) -> list[str]:
        """Return the full business stage pipeline for an object type."""
        pipelines = {
            "lead": ["Inquiry", "Qualified", "Proposal Sent", "Negotiating", "Converted", "Closed"],
            "proposal": ["Drafting", "Shared", "Viewed", "Under Discussion", "Approved", "Converted", "Completed"],
            "invoice": ["Drafting", "Sent", "Viewed", "Paid", "Overdue", "Cancelled"],
            "customer": ["Acquired", "Active", "Growing", "VIP Engagement", "Dormant", "Churned"],
            "task": ["Queued", "Working", "Blocked", "Done", "Cancelled"],
            "conversation": ["Active", "Awaiting Reply", "Resolved", "Archived"],
            "project": ["Planning", "Executing", "On Hold", "Delivered", "Cancelled"],
        }
        return pipelines.get(obj_type, ["Created", "Updated", "Active", "Completed"])

    def _build_stage_history(self, obj_type: str, records: list[dict]) -> list[dict]:
        """Build a stage history from records."""
        stage_milestones = []
        sorted_records = sorted(
            records,
            key=lambda r: r.get("created_at") or "",
            reverse=True,
        )
        for rec in sorted_records[:5]:
            stage = self._derive_business_stage(obj_type, rec["status"])
            stage_milestones.append({
                "stage": stage,
                "timestamp": rec["updated_at"] or rec["created_at"],
                "label": f"Moved to {stage}",
                "actor": rec.get("data", {}).get("updated_by", "System"),
            })
        return stage_milestones

    def _build_relationship_story(self, obj_type: str, records: list[dict]) -> list[dict]:
        """Build relationship entries that explain WHY each exists.

        Each relationship tells a business story instead of just listing linked records.
        """
        stories: list[dict] = []
        obj_type = obj_type or ""

        # Use Universal Graph to find real relationships
        try:
            for rec in records[:3]:
                oid = rec["object_id"]
                rels = self._rel_store.get_for_entity(oid)
                for rel in rels:
                    # Infer a business explanation
                    explanation = self._explain_relationship(rel, oid)
                    stories.append({
                        "direction": "outbound" if rel.source_id == oid else "inbound",
                        "type": rel.rel_type,
                        "target_id": rel.target_id,
                        "target_name": self._resolve_entity_name(rel.target_id) if rel.target_id != oid
                                       else self._resolve_entity_name(rel.source_id),
                        "explanation": explanation or f"Connected via {rel.rel_type}",
                        "confidence": rel.confidence,
                    })
        except Exception:
            pass

        # If no graph relationships, provide type-aware default explanations
        if not stories:
            # Business-flow explanations per object type
            flow_map = {
                "lead": [
                    {"target": "Conversation", "explanation": "Conversation started from this inquiry"},
                    {"target": "Proposal", "explanation": "Proposal generated from qualified lead"},
                ],
                "customer": [
                    {"target": "Conversation", "explanation": "All conversations with this customer"},
                    {"target": "Invoice", "explanation": "Billing history for this customer"},
                    {"target": "Proposal", "explanation": "Proposals sent to this customer"},
                ],
                "proposal": [
                    {"target": "Conversation", "explanation": "Created from this negotiation"},
                    {"target": "Invoice", "explanation": "Invoice generated from this proposal"},
                ],
                "invoice": [
                    {"target": "Customer", "explanation": "Billed to this customer"},
                    {"target": "Payment", "explanation": "Payment awaiting confirmation"},
                ],
            }
            default_flow = flow_map.get(obj_type, [{"target": "Related Object", "explanation": "Connected business entity"}])
            for item in default_flow:
                stories.append({
                    "direction": "outbound",
                    "type": "relates_to",
                    "target_id": "",
                    "target_name": item["target"],
                    "explanation": item["explanation"],
                    "confidence": 0.5,
                })

        return stories

    def _explain_relationship(self, rel, entity_id: str) -> str:
        """Return a natural-language explanation for a relationship."""
        explanations = {
            "manages": "Oversees this entity",
            "owns": "Owned by this entity",
            "partners_with": "Strategic partnership",
            "belongs_to": "Associated with",
            "reports_to": "Reports to",
            "created": "Initiated by",
            "generated_from": "Generated from this source",
            "billed_to": "Billed to this customer",
            "paid_by": "Payment from",
            "relates_to": "Connected entity",
        }
        default = f"Linked via {rel.rel_type}"
        return explanations.get(rel.rel_type, default)

    def _resolve_entity_name(self, entity_id: str) -> str:
        """Resolve an entity ID to a human-readable name."""
        try:
            entity = self._entity_store.get(entity_id)
            if entity:
                return entity.name
        except Exception:
            pass
        return entity_id

    def _build_time_narrative(self, records: list[dict]) -> str:
        """Transform raw timestamps into a business-meaningful time narrative."""
        if not records:
            return "No activity recorded"

        latest = max(
            (r.get("updated_at") or r.get("created_at") or "") for r in records
        )
        if not latest:
            return "No activity recorded"

        try:
            if isinstance(latest, str):
                latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
            else:
                latest_dt = latest
            now = datetime.now(timezone.utc)
            delta = now - latest_dt
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60

            if days > 30:
                months = days // 30
                return f"No activity for {months} month{'s' if months > 1 else ''}"
            if days > 0:
                return f"Last activity {days} day{'s' if days > 1 else ''} ago"
            if hours > 0:
                return f"Last activity {hours} hour{'s' if hours > 1 else ''} ago"
            if minutes > 0:
                return f"Updated {minutes} minute{'s' if minutes > 1 else ''} ago"
            return "Updated just now"
        except Exception:
            return latest[:10] if isinstance(latest, str) else "Recently"

    def _build_object_recommendation(self, obj_type: str, status: str, records: list[dict]) -> dict:
        """Build a context-aware recommendation for this object type.

        Every object concludes with advice, not data.
        """
        now = datetime.now(timezone.utc)
        latest_record = records[0] if records else {}
        latest_ts = latest_record.get("updated_at") or latest_record.get("created_at")

        # Calculate time since last update
        hours_since_update = 0
        if latest_ts:
            try:
                if isinstance(latest_ts, str):
                    dt = datetime.fromisoformat(latest_ts.replace("Z", "+00:00"))
                    hours_since_update = max(1, (now - dt).seconds // 3600)
            except Exception:
                pass

        recommendations = {
            "lead": [
                {"condition": lambda s, h: s == "new" and h > 24,
                 "label": "Send Follow-up", "type": "outcome",
                 "confidence": 0.85,
                 "reasoning": "Lead has been waiting {h} hour(s). First response within 5 minutes improves close rate by 50%."},
                {"condition": lambda s, h: s == "new",
                 "label": "Qualify Lead", "type": "outcome",
                 "confidence": 0.9,
                 "reasoning": "New lead requires qualification to determine next steps."},
                {"condition": lambda s, h: s == "proposal",
                 "label": "Follow Up on Proposal", "type": "outcome",
                 "confidence": 0.8,
                 "reasoning": "Proposal has been pending for {h} hour(s). Timely follow-up increases conversion."},
                {"condition": lambda s, h: True,
                 "label": "Review Lead Status", "type": "navigate",
                 "confidence": 0.6,
                 "reasoning": "Regular review ensures no opportunity is missed."},
            ],
            "proposal": [
                {"condition": lambda s, h: s == "draft",
                 "label": "Complete & Send Proposal", "type": "outcome",
                 "confidence": 0.9,
                 "reasoning": "Proposal is still in draft. Completing it unlocks the next stage."},
                {"condition": lambda s, h: s == "sent" and h > 48,
                 "label": "Send Gentle Reminder", "type": "outcome",
                 "confidence": 0.8,
                 "reasoning": "Proposal viewed {h} hour(s) ago without response. A brief check-in is appropriate."},
                {"condition": lambda s, h: s == "viewed",
                 "label": "Prepare Discussion Points", "type": "outcome",
                 "confidence": 0.85,
                 "reasoning": "Proposal was viewed. The customer is evaluating — prepare to address questions."},
                {"condition": lambda s, h: True,
                 "label": "Check Proposal Status", "type": "navigate",
                 "confidence": 0.5,
                 "reasoning": "Proposal requires attention."},
            ],
            "invoice": [
                {"condition": lambda s, h: s == "overdue",
                 "label": "Send Payment Reminder", "type": "outcome",
                 "confidence": 0.9,
                 "reasoning": "Invoice is overdue for {h} hour(s). Early follow-up increases collection rate."},
                {"condition": lambda s, h: s == "sent" and h > 72,
                 "label": "Check Payment Status", "type": "outcome",
                 "confidence": 0.7,
                 "reasoning": "Invoice sent {h} hour(s) ago without confirmation."},
                {"condition": lambda s, h: True,
                 "label": "Record Payment", "type": "outcome",
                 "confidence": 0.8,
                 "reasoning": "Keeping payment records up to date ensures accurate financial tracking."},
            ],
            "customer": [
                {"condition": lambda s, h: s in ("active", "vip") and h > 168,
                 "label": "Check In with Customer", "type": "outcome",
                 "confidence": 0.8,
                 "reasoning": "Customer has been inactive for {days} day(s). Regular contact strengthens relationships."},
                {"condition": lambda s, h: s == "dormant",
                 "label": "Re-engagement Campaign", "type": "outcome",
                 "confidence": 0.7,
                 "reasoning": "Dormant customers are easier to re-engage than acquire new ones."},
                {"condition": lambda s, h: True,
                 "label": "Review Customer Health", "type": "navigate",
                 "confidence": 0.6,
                 "reasoning": "Regular health checks prevent churn and identify growth opportunities."},
            ],
        }

        type_recs = recommendations.get(obj_type, [
            {"condition": lambda s, h: True,
             "label": "Update Record", "type": "outcome",
             "confidence": 0.7,
             "reasoning": "Keeping records current ensures SHUNYA provides accurate insights."},
        ])

        # Find the best matching recommendation
        for rec in type_recs:
            if rec["condition"](status, hours_since_update):
                # Fix f-strings that need actual variable values
                rec["reasoning"] = rec["reasoning"].format(
                    h=hours_since_update,
                    days=max(1, hours_since_update // 24),
                )
                return rec

        # Fallback
        return {
            "label": "Review Record",
            "type": "navigate",
            "confidence": 0.5,
            "reasoning": f"This {obj_type} record is up to date. Regular review is recommended.",
        }

    def _build_active_executions(self, identity_id: str) -> list[dict]:
        """Get currently active executions."""
        executions = []
        try:
            outcomes = Outcome.query.filter(
                Outcome.stage.in_(["accepted", "queued", "executing"]),
                Outcome.identity_id == identity_id,
            ).order_by(Outcome.created_at.desc()).limit(10).all()
            for o in outcomes:
                executions.append({
                    "id": o.outcome_id,
                    "label": o.intention[:80],
                    "description": f"Stage: {o.stage}",
                    "status": "in_progress" if o.stage == "executing" else "pending",
                    "progress": 0.5 if o.stage == "executing" else 0.2,
                    "started_at": o.created_at.isoformat() if o.created_at else None,
                })
        except Exception:
            pass
        return executions

    def _build_recent_outcomes(self, identity_id: str) -> list[dict]:
        """Get recent completed/failed outcomes."""
        outcomes = []
        try:
            recent = Outcome.query.filter(
                Outcome.identity_id == identity_id,
            ).order_by(Outcome.created_at.desc()).limit(5).all()
            for o in recent:
                is_success = o.stage in ("completed", "success")
                outcomes.append({
                    "id": o.outcome_id,
                    "label": o.intention[:80],
                    "status": "completed" if is_success else "failed",
                    "outcome": o.progress or "",
                    "error": getattr(o, 'error', None),
                    "timestamp": o.created_at.isoformat() if o.created_at else None,
                })
        except Exception:
            pass
        return outcomes

    def _build_org_summary(self, identity_id: str) -> dict:
        """Build executive summary of the organization."""
        summary = {"total_objects": 0, "by_type": {}, "active_executions": 0}
        try:
            rows = db.session.execute(
                "SELECT object_type, COUNT(*) as cnt FROM sh_objects "
                "WHERE is_deleted = false GROUP BY object_type"
            ).fetchall()
            for row in rows:
                summary["by_type"][row[0]] = row[1]
                summary["total_objects"] += row[1]

            exec_count = Outcome.query.filter(
                Outcome.stage.in_(["accepted", "queued", "executing"]),
                Outcome.identity_id == identity_id,
            ).count()
            summary["active_executions"] = exec_count
        except Exception:
            pass
        return summary

    def _build_cognition(self, identity_id: str) -> dict:
        """Build AI cognition summary — what SHUNYA is thinking.

        This is the "continuously thinking" surface from LX-02 §6.
        """
        try:
            obs_store = get_obs_store()
            active_obs = [o for o in obs_store._observations.values()
                         if o.status.value == "active"]
            compiler = get_compiler()
            insights = compiler.compile_all()

            return {
                "observations": [
                    {"label": o.label, "confidence": o.confidence,
                     "description": o.description[:120], "age_hours": getattr(o, 'age_hours', 0)}
                    for o in active_obs[:5]
                ],
                "insights": [
                    {"label": i.label, "detail": i.detail[:120], "confidence": i.confidence}
                    for i in insights[:5]
                ],
                "monitoring_count": len(active_obs),
                "insight_count": len(insights),
            }
        except Exception:
            return {"observations": [], "insights": [], "monitoring_count": 0, "insight_count": 0}

    def _filter_events_for_workspace(
        self, events: list[RealityEvent], workspace_type: str
    ) -> list[RealityEvent]:
        """Filter reality events by workspace relevance."""
        type_filters = {
            "founder": lambda e: True,  # Founder sees everything
            "finance": lambda e: e.object_type in ("invoice", "payment", "expense", "budget") or e.source == "execution",
            "travel": lambda e: e.object_type in ("travel", "trip", "booking", "itinerary", "customer"),
            "business": lambda e: e.object_type in ("customer", "proposal", "invoice", "task", "project", "lead"),
            "personal": lambda e: e.object_type in ("note", "task", "goal", "learning", "contact"),
            "studio": lambda e: e.object_type in ("content", "media", "integration", "file", "template"),
        }
        filter_fn = type_filters.get(workspace_type, lambda e: True)
        return [e for e in events if filter_fn(e)]

    def _filter_objects_for_workspace(
        self, objects: list[dict], workspace_type: str
    ) -> list[dict]:
        """Filter living objects by workspace relevance."""
        type_filters = {
            "founder": lambda o: True,
            "finance": lambda o: o.get("object_type") in ("invoice", "payment", "expense", "budget"),
            "travel": lambda o: o.get("object_type") in ("travel", "trip", "booking", "itinerary", "customer", "lead"),
            "business": lambda o: o.get("object_type") in ("customer", "proposal", "invoice", "task", "project", "lead", "contact", "organization"),
            "personal": lambda o: o.get("object_type") in ("note", "task", "goal", "learning", "contact"),
            "studio": lambda o: o.get("object_type") in ("content", "media", "integration", "file", "template"),
        }
        filter_fn = type_filters.get(workspace_type, lambda o: True)
        return [o for o in objects if filter_fn(o)]

    def _build_workspace_briefing(self, workspace_type: str, snapshot: RealitySnapshot) -> dict:
        """Build a workspace-specific briefing."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
        org_summary = snapshot.organization_summary

        return {
            "time_of_day": time_of_day,
            "event_count": len(snapshot.events),
            "attention_count": len(snapshot.attention_queue),
            "object_count": org_summary.get("total_objects", 0),
            "execution_count": org_summary.get("active_executions", 0),
            "top_attention": snapshot.attention_queue[:3] if snapshot.attention_queue else [],
        }

    def _build_demo_snapshot(self) -> RealitySnapshot:
        """Build a demonstration snapshot for the Demonstration Tenant.

        Uses the same data pipeline as every other workspace. The demonstration
        tenant is a canonical SHUNYA tenant — not a special code path.
        """
        from datetime import timedelta, timezone
        now = datetime.now(timezone.utc)
        events = [
            RealityEvent(
                event_id="demo-evt-001",
                type=RealityEventType.OBJECT_UPDATED,
                title="Customer accepted revised proposal",
                description="GlobalTech accepted the revised proposal for Q3 engagement",
                timestamp=(now - timedelta(minutes=10)).isoformat(),
                actor="Sarah Chen",
                importance="high",
                confidence=1.0,
                object_type="proposal",
                object_id="demo-prop-001",
                object_name="Q3 GlobalTech Proposal",
            ),
            RealityEvent(
                event_id="demo-evt-002",
                type=RealityEventType.OBJECT_CREATED,
                title="Supplier delayed shipment by 2 days",
                description="Acme Manufacturing delayed order #1042 — original delivery Aug 5, now Aug 7",
                timestamp=(now - timedelta(minutes=15)).isoformat(),
                actor="Acme Manufacturing",
                importance="high",
                confidence=1.0,
                object_type="order",
                object_id="demo-ord-001",
                object_name="Order #1042",
            ),
            RealityEvent(
                event_id="demo-evt-003",
                type=RealityEventType.OBJECT_UPDATED,
                title="Payment cleared this morning",
                description="Invoice INV-004 payment of $4,200 received from Acme Corp",
                timestamp=(now - timedelta(minutes=90)).isoformat(),
                actor="Acme Corp",
                importance="normal",
                confidence=1.0,
                object_type="payment",
                object_id="demo-pmt-001",
                object_name="INV-004 Payment",
            ),
        ]
        attention_queue = [
            {
                "item_id": "demo-attn-001",
                "label": "Supplier delay affects 3 shipments",
                "description": "Order #1042 delay impacts shipments scheduled for Aug 5, 6, and 8",
                "source_type": "reality",
                "source_id": "demo-ord-001",
                "priority_score": 0.85,
            },
            {
                "item_id": "demo-attn-002",
                "label": "Proposal accepted — next steps required",
                "description": "Contract signing, scheduling, and resource allocation pending for GlobalTech proposal",
                "source_type": "reality",
                "source_id": "demo-prop-001",
                "priority_score": 0.72,
            },
        ]
        living_objects = [
            {
                "id": "demo-obj-001",
                "object_id": "demo-obj-001",
                "object_type": "proposal",
                "name": "Q3 GlobalTech Proposal",
                "count": 1,
                "current_stage": "Accepted",
                "stage_history": [{"stage": "Draft", "entered_at": "2026-07-20T08:00:00Z"},
                    {"stage": "Under Review", "entered_at": "2026-07-28T08:00:00Z"},
                    {"stage": "Accepted", "entered_at": (now - timedelta(minutes=10)).isoformat()}],
                "summary": "1 proposal",
                "time_narrative": "Accepted 10 minutes ago",
                "recommendation": {"label": "Begin contract signing", "type": "action", "confidence": 0.85, "reasoning": "Proposal accepted. Next step is contract signing and resource allocation."},
            },
            {
                "id": "demo-obj-002",
                "object_id": "demo-obj-002",
                "object_type": "order",
                "name": "Order #1042",
                "count": 1,
                "current_stage": "Delayed",
                "stage_history": [{"stage": "Placed", "entered_at": "2026-07-28T08:00:00Z"},
                    {"stage": "Confirmed", "entered_at": "2026-07-28T12:00:00Z"},
                    {"stage": "Delayed", "entered_at": (now - timedelta(minutes=15)).isoformat()}],
                "summary": "1 order",
                "time_narrative": "Delayed 15 minutes ago",
                "recommendation": {"label": "Review supplier contract", "type": "action", "confidence": 0.72, "reasoning": "Supplier delays are increasing. Contract review recommended."},
            },
        ]
        return RealitySnapshot(
            snapshot_id=f"demo_snap_{uuid.uuid4().hex[:12]}",
            timestamp=now.isoformat(),
            events=events,
            attention_queue=attention_queue,
            living_objects=living_objects,
            active_executions=[],
            recent_outcomes=[],
            organization_summary={"total_objects": 3, "active_executions": 0},
            cognition={
                "observations": [
                    {"label": "Supplier delays are increasing", "confidence": 0.88,
                     "description": "3 delays in 30 days — two from same supplier", "age_hours": 0},
                    {"label": "These events share a hidden relationship", "confidence": 0.94,
                     "description": "Proposal, supplier delay, and payment are consequences of the same commitment", "age_hours": 0},
                ],
                "insights": [],
                "monitoring_count": 2,
                "insight_count": 0,
            },
        )


# ═════════════════════════════════════════════════════════════════════
# Module-level singleton
# ═════════════════════════════════════════════════════════════════════

_ENGINE_INSTANCE: Optional[RealityEngine] = None


def get_reality_engine() -> RealityEngine:
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = RealityEngine()
    return _ENGINE_INSTANCE


def reset_reality_engine() -> None:
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None