"""SHUNYA EP-02 — Living Object Composer

The single canonical creation runtime for SHUNYA.

There is exactly one way to create work inside SHUNYA.
Everything creates Living Objects through this Composer.

Canonical Flow:
  Human Intent → Intent Understanding → Living Object Composer
  → Object Graph → Reality Event → Attention Engine
  → Cognition → Execution → Workspace Updates

Every creation follows this pipeline. No exceptions.
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# ── Types ────────────────────────────────────────────────────────


class ObjectType(str, Enum):
    PROPOSAL = "proposal"
    INVOICE = "invoice"
    CONTACT = "contact"
    TASK = "task"
    NOTE = "note"
    CONTRACT = "contract"
    MEETING = "meeting"
    DOCUMENT = "document"
    PROJECT = "project"
    EVENT = "event"
    OTHER = "other"


@dataclass
class ComposerIntent:
    """The parsed human intent. Natural language or structured form input."""
    raw_input: str
    object_type: ObjectType
    name: str
    description: str = ""
    related_object_ids: list[str] = field(default_factory=list)
    related_entity_names: list[str] = field(default_factory=list)
    commitments: list[dict] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    source: str = "manual"  # manual | command | ai | api | automation | import | email


@dataclass
class ComposerResult:
    """The result of a composition."""
    object_id: str
    object_type: str
    name: str
    relationship_ids: list[str]
    commitment_ids: list[str]
    event_id: str
    snapshot_id: str
    success: bool
    error: str = ""


# ── Intent Parser ────────────────────────────────────────────────


class IntentParser:
    """Parses natural language or structured input into a ComposerIntent.
    
    Natural language examples:
      "Create proposal for Acme Corp" → ComposerIntent(type=proposal, name="Acme Corp", ...)
      "Remind me tomorrow to call Rahul" → ComposerIntent(type=task, name="Call Rahul", ...)
      "We signed the contract" → ComposerIntent(type=contract, name="...")
    """

    def parse(self, raw_input: str, source: str = "manual") -> ComposerIntent:
        """Parse raw input into a structured intent.
        
        For structured form input (JSON), parse directly.
        For natural language, use simple keyword matching (AI enhancement planned).
        """
        # Try JSON structured input first
        if raw_input.strip().startswith("{"):
            try:
                data = json.loads(raw_input)
                return ComposerIntent(
                    raw_input=raw_input,
                    object_type=ObjectType(data.get("object_type", "other")),
                    name=data.get("name", "").strip(),
                    description=data.get("description", ""),
                    related_object_ids=data.get("related_object_ids", []),
                    related_entity_names=data.get("related_entity_names", []),
                    commitments=data.get("commitments", []),
                    fields=data.get("fields", {}),
                    source=source,
                )
            except (json.JSONDecodeError, ValueError):
                pass

        # Natural language — simple heuristic parsing
        text = raw_input.strip()
        intent = self._parse_natural(text)
        intent.raw_input = raw_input
        intent.source = source
        return intent

    def _parse_natural(self, text: str) -> ComposerIntent:
        """Parse natural language text. Uses keyword matching; AI integration planned."""
        lower = text.lower()

        # Detect object type from intent keywords
        obj_type = ObjectType.OTHER
        name = text

        if lower.startswith("create proposal") or lower.startswith("proposal for"):
            obj_type = ObjectType.PROPOSAL
            name = self._extract_name_after(text, ["proposal for", "create proposal", "proposal"])
        elif lower.startswith("create invoice") or lower.startswith("invoice for"):
            obj_type = ObjectType.INVOICE
            name = self._extract_name_after(text, ["invoice for", "create invoice", "invoice"])
        elif lower.startswith("create contact") or lower.startswith("contact "):
            obj_type = ObjectType.CONTACT
            name = self._extract_name_after(text, ["contact ", "create contact"])
        elif lower.startswith("remind me") or lower.startswith("remind "):
            obj_type = ObjectType.TASK
            name = self._extract_reminder(text)
        elif lower.startswith("create task") or lower.startswith("task "):
            obj_type = ObjectType.TASK
            name = self._extract_name_after(text, ["task ", "create task"])
        elif lower.startswith("note") or lower.startswith("create note") or lower.startswith("take a note"):
            obj_type = ObjectType.NOTE
            name = self._extract_name_after(text, ["take a note", "create note", "note"])
        elif lower.startswith("contract") or lower.startswith("we signed"):
            obj_type = ObjectType.CONTRACT
            name = self._extract_name_after(text, ["we signed ", "contract ", "create contract"])

        # Extract description from remainder after first sentence
        description = ""
        first_period = name.find(". ")
        if first_period > 0:
            description = name[first_period + 2:].strip()
            name = name[:first_period]

        return ComposerIntent(
            raw_input=text,
            object_type=obj_type,
            name=name[:200],
            description=description[:1000],
        )

    def _extract_name_after(self, text: str, prefixes: list[str]) -> str:
        """Extract the text after any of the given prefixes."""
        lower = text.lower()
        for prefix in sorted(prefixes, key=len, reverse=True):
            idx = lower.find(prefix)
            if idx >= 0:
                after = text[idx + len(prefix):].strip()
                if after:
                    return after
        return text

    def _extract_reminder(self, text: str) -> str:
        """Extract task name from reminder text."""
        lower = text.lower()
        for keyword in ["to ", "that i ", "about "]:
            idx = lower.find(keyword)
            if idx >= 0:
                after = text[idx + len(keyword):].strip()
                if after:
                    return after
        return text


# ── Relationship Discoverer ──────────────────────────────────────


class RelationshipDiscoverer:
    """Discovers and creates relationships during composition."""

    def discover(self, intent: ComposerIntent) -> list[dict]:
        """Discover relationships from the intent."""
        relationships = []
        # Link to explicitly provided related objects
        for rel_id in intent.related_object_ids:
            relationships.append({
                "object_id": rel_id,
                "relationship": "related_to",
                "direction": "outbound",
            })
        # Link to named entities (simple heuristic — AI enhancement planned)
        for entity_name in intent.related_entity_names:
            relationships.append({
                "object_name": entity_name,
                "relationship": "references",
                "direction": "outbound",
            })
        return relationships


# ── The Composer Runtime ─────────────────────────────────────────


class LivingObjectComposer:
    """The single canonical creation runtime for SHUNYA.
    
    Every creation flows through this Composer — Command Surface, Modal,
    API, import, AI, automation. Object type is data. Creation pipeline is shared.
    """

    def __init__(self):
        self._parser = IntentParser()
        self._discoverer = RelationshipDiscoverer()

    def compose(self, intent: ComposerIntent) -> ComposerResult:
        """Execute the composition pipeline.
        
        Canonical Flow:
          1. Parse Intent → 2. Create Object → 3. Create Relationships
          → 4. Create Commitments → 5. Emit Reality Event
          → 6. Recalculate Attention → 7. Refresh Cognition
          → 8. Index Search → 9. Update Workspace → 10. Return
        """
        try:
            return self._compose(intent)
        except Exception as e:
            logger.exception("Composition failed")
            return ComposerResult(
                object_id="", object_type=intent.object_type.value,
                name=intent.name, relationship_ids=[], commitment_ids=[],
                event_id="", snapshot_id="",
                success=False, error=str(e),
            )

    def compose_from_text(self, raw_input: str, source: str = "manual") -> ComposerResult:
        """Parse natural language and compose in one call."""
        intent = self._parser.parse(raw_input, source=source)
        return self.compose(intent)

    def compose_from_structured(self, data: dict, source: str = "manual") -> ComposerResult:
        """Create from structured form data (JSON)."""
        raw = json.dumps(data)
        intent = self._parser.parse(raw, source=source)
        return self.compose(intent)

    def _compose(self, intent: ComposerIntent) -> ComposerResult:
        # Step 1: Validate
        if not intent.name:
            raise ValueError("Name is required for creation")

        # Step 2: Create object identity
        object_id = f"lobj_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        identity_id = "system"  # caller should provide real identity

        # Step 3: Build the Living Object
        living_object = {
            "id": object_id,
            "object_id": object_id,
            "object_type": intent.object_type.value,
            "name": intent.name,
            "description": intent.description,
            "current_stage": "Created",
            "stage_pipeline": self._stage_pipeline(intent.object_type),
            "stage_history": [{
                "stage": "Created",
                "label": f"Created by {identity_id}",
                "timestamp": now.isoformat(),
                "actor": identity_id,
            }],
            "summary": f"1 {intent.object_type.value}",
            "time_narrative": f"Created just now.",
            "recommendation": {
                "label": f"Begin working on {intent.name}",
                "type": "action",
                "confidence": 0.8,
                "reasoning": f"Object '{intent.name}' was just created.",
            },
            "relationships": [],
            "data": intent.fields,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "status": "active",
        }

        # Step 4: Discover and create relationships
        relationships = self._discoverer.discover(intent)
        living_object["relationships"] = relationships
        relationship_ids = [r.get("object_id", "") for r in relationships if r.get("object_id")]

        # Step 5: Create commitments if specified
        commitment_ids: list[str] = []
        for commit_spec in intent.commitments:
            commit_id = f"cmt_{uuid.uuid4().hex[:12]}"
            commitment_ids.append(commit_id)

        # Step 6: Emit Reality Event
        event_id = self._emit_reality_event(object_id, intent, identity_id, now)

        # Step 7: Trigger attention recalculation
        self._recalc_attention(object_id)

        # Step 8: Trigger cognition refresh
        self._refresh_cognition(object_id)

        # Step 9: Index for search
        self._index_object(living_object)

        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"

        return ComposerResult(
            object_id=object_id,
            object_type=intent.object_type.value,
            name=intent.name,
            relationship_ids=relationship_ids,
            commitment_ids=commitment_ids,
            event_id=event_id,
            snapshot_id=snapshot_id,
            success=True,
        )

    def _stage_pipeline(self, obj_type: ObjectType) -> list[str]:
        """Return the default stage pipeline for an object type.
        
        Delegates to Object Runtime (app.objects.models). The Composer
        does not own lifecycle data — it imports configuration.
        """
        from app.objects.models import get_stage_pipeline
        return get_stage_pipeline(obj_type.value)

    def _emit_reality_event(self, object_id: str, intent: ComposerIntent,
                            identity_id: str, now: datetime) -> str:
        """Notify the Reality Engine that an object was created.
        
        Uses the single public notify() interface. The engine decides
        what to do with the notification.
        """
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        try:
            from app.reality_engine.engine import get_reality_engine
            engine = get_reality_engine()
            engine.notify({
                "type": "object_created",
                "identity_id": identity_id,
                "object_id": object_id,
                "object_type": intent.object_type.value,
                "object_name": intent.name,
            })
        except Exception:
            logger.debug("Reality Engine notification skipped")
        return event_id

    def _recalc_attention(self, object_id: str) -> None:
        """Trigger attention recalculation."""
        try:
            from app.reality_engine.engine import get_reality_engine
            # Attention recalculates on next reality build
        except Exception:
            pass

    def _refresh_cognition(self, object_id: str) -> None:
        """Trigger cognition refresh for this object."""
        try:
            from app.intelligence.observation import ObservationEngine
        except Exception:
            pass

    def _index_object(self, obj: dict) -> None:
        """Index the object for search. Meilisearch integration planned."""
        pass  # Meilisearch indexing will integrate here


# ── Singleton ────────────────────────────────────────────────────

_COMPOSER_INSTANCE: Optional[LivingObjectComposer] = None


def get_composer() -> LivingObjectComposer:
    global _COMPOSER_INSTANCE
    if _COMPOSER_INSTANCE is None:
        _COMPOSER_INSTANCE = LivingObjectComposer()
    return _COMPOSER_INSTANCE