"""Business Ontology Model — the canonical representation of a discovered business.

An ontology describes what a business is, does, serves, creates, measures, and needs.
It is the intermediate representation between conversation and modules.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# ── Enums ─────────────────────────────────────────────────────────────────


class OntologyEntityType(str, enum.Enum):
    PRIMARY = "primary"      # Core business entities (Customer, Invoice)
    SECONDARY = "secondary"  # Supporting entities (Notes, Attachments)
    REFERENCE = "reference"  # Lookup/taxonomy entities (Category, Status)
    VIRTUAL = "virtual"      # Computed/report entities


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"           # ≥85% — auto-apply
    MEDIUM = "medium"       # 60-84% — suggest, ask for confirmation
    LOW = "low"             # 30-59% — ask clarifying questions
    UNCERTAIN = "uncertain" # <30% — skip until more data


class RelationshipCardinality(str, enum.Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class LifecycleStageType(str, enum.Enum):
    INITIAL = "initial"
    INTERMEDIATE = "intermediate"
    FINAL = "final"


# ── Core Data Types ──────────────────────────────────────────────────────


@dataclass
class EntityField:
    """A field within an ontology entity."""
    key: str
    label: str
    field_type: str  # Mirrors FieldType enum values
    required: bool = False
    searchable: bool = True
    display_in_list: bool = True
    options: list[str] | None = None
    default: str | None = None
    order: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> EntityField:
        d = dict(d)
        if "confidence" in d and isinstance(d["confidence"], str):
            try:
                d["confidence"] = ConfidenceLevel(d["confidence"])
            except ValueError:
                d["confidence"] = ConfidenceLevel.MEDIUM
        return cls(**d)


@dataclass
class EntityRelationship:
    """A relationship between two ontology entities."""
    source_entity: str
    target_entity: str
    cardinality: RelationshipCardinality = RelationshipCardinality.ONE_TO_MANY
    label: str = ""
    inverse_label: str = ""
    required: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cardinality"] = self.cardinality.value
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> EntityRelationship:
        d = dict(d)
        if "cardinality" in d and isinstance(d["cardinality"], str):
            try:
                d["cardinality"] = RelationshipCardinality(d["cardinality"])
            except ValueError:
                d["cardinality"] = RelationshipCardinality.ONE_TO_MANY
        if "confidence" in d and isinstance(d["confidence"], str):
            try:
                d["confidence"] = ConfidenceLevel(d["confidence"])
            except ValueError:
                d["confidence"] = ConfidenceLevel.MEDIUM
        return cls(**d)


@dataclass
class LifecycleStage:
    """A stage in an entity lifecycle."""
    key: str
    label: str
    stage_type: LifecycleStageType = LifecycleStageType.INTERMEDIATE
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stage_type"] = self.stage_type.value
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> LifecycleStage:
        d = dict(d)
        if "stage_type" in d and isinstance(d["stage_type"], str):
            try:
                d["stage_type"] = LifecycleStageType(d["stage_type"])
            except ValueError:
                d["stage_type"] = LifecycleStageType.INTERMEDIATE
        if "confidence" in d and isinstance(d["confidence"], str):
            try:
                d["confidence"] = ConfidenceLevel(d["confidence"])
            except ValueError:
                d["confidence"] = ConfidenceLevel.MEDIUM
        return cls(**d)


@dataclass
class EntityDef:
    """A discovered business entity."""
    key: str
    name: str
    plural_name: str = ""
    description: str = ""
    entity_type: OntologyEntityType = OntologyEntityType.PRIMARY
    fields: list[EntityField] = field(default_factory=list)
    lifecycle: list[LifecycleStage] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    common_intents: list[str] = field(default_factory=list)
    icon: str = "📦"
    color: str = "#6366f1"
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def __post_init__(self):
        if not self.plural_name:
            self.plural_name = self.name + "s"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["entity_type"] = self.entity_type.value
        d["fields"] = [f.to_dict() for f in self.fields]
        d["lifecycle"] = [l.to_dict() for l in self.lifecycle]
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> EntityDef:
        d = dict(d)
        if "entity_type" in d and isinstance(d["entity_type"], str):
            try:
                d["entity_type"] = OntologyEntityType(d["entity_type"])
            except ValueError:
                d["entity_type"] = OntologyEntityType.PRIMARY
        if "fields" in d:
            d["fields"] = [EntityField.from_dict(f) for f in d["fields"]]
        if "lifecycle" in d:
            d["lifecycle"] = [LifecycleStage.from_dict(l) for l in d["lifecycle"]]
        if "confidence" in d and isinstance(d["confidence"], str):
            try:
                d["confidence"] = ConfidenceLevel(d["confidence"])
            except ValueError:
                d["confidence"] = ConfidenceLevel.MEDIUM
        return cls(**d)


@dataclass
class InferredMetric:
    """A metric/KPI discovered for the business."""
    key: str
    label: str
    description: str = ""
    entity: str = ""
    field: str = ""
    aggregation: str = "count"  # count, sum, avg, min, max
    filter_criteria: str = ""
    icon: str = "📊"
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> InferredMetric:
        d = dict(d)
        if "confidence" in d and isinstance(d["confidence"], str):
            try:
                d["confidence"] = ConfidenceLevel(d["confidence"])
            except ValueError:
                d["confidence"] = ConfidenceLevel.MEDIUM
        return cls(**d)


@dataclass
class InferredAutomation:
    """A task that could be automated."""
    key: str
    label: str
    description: str = ""
    trigger: str = ""  # event that starts this
    action: str = ""   # action to perform
    conditions: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = self.confidence.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> InferredAutomation:
        d = dict(d)
        if "confidence" in d and isinstance(d["confidence"], str):
            try:
                d["confidence"] = ConfidenceLevel(d["confidence"])
            except ValueError:
                d["confidence"] = ConfidenceLevel.MEDIUM
        return cls(**d)


@dataclass
class BusinessOntology:
    """Complete business ontology — the canonical representation of a discovered business."""
    key: str
    name: str
    description: str = ""
    industry: str = ""
    entities: list[EntityDef] = field(default_factory=list)
    relationships: list[EntityRelationship] = field(default_factory=list)
    metrics: list[InferredMetric] = field(default_factory=list)
    automations: list[InferredAutomation] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    terminology: dict[str, str] = field(default_factory=dict)  # synonym → canonical
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def get_entity(self, key: str) -> EntityDef | None:
        for e in self.entities:
            if e.key == key:
                return e
        return None

    def get_related_entities(self, entity_key: str) -> list[str]:
        """Get entity keys related to the given entity."""
        related = []
        for r in self.relationships:
            if r.source_entity == entity_key:
                related.append(r.target_entity)
            if r.target_entity == entity_key:
                related.append(r.source_entity)
        return related

    def overall_confidence(self) -> float:
        """Average confidence across all discovered components."""
        scores = []
        for e in self.entities:
            scores.append(_confidence_score(e.confidence))
            for f in e.fields:
                scores.append(_confidence_score(f.confidence))
            for s in e.lifecycle:
                scores.append(_confidence_score(s.confidence))
        for r in self.relationships:
            scores.append(_confidence_score(r.confidence))
        for m in self.metrics:
            scores.append(_confidence_score(m.confidence))
        for a in self.automations:
            scores.append(_confidence_score(a.confidence))
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["entities"] = [e.to_dict() for e in self.entities]
        d["relationships"] = [r.to_dict() for r in self.relationships]
        d["metrics"] = [m.to_dict() for m in self.metrics]
        d["automations"] = [a.to_dict() for a in self.automations]
        d["overall_confidence"] = self.overall_confidence()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> BusinessOntology:
        d = dict(d)
        if "entities" in d:
            d["entities"] = [EntityDef.from_dict(e) for e in d["entities"]]
        if "relationships" in d:
            d["relationships"] = [EntityRelationship.from_dict(r) for r in d["relationships"]]
        if "metrics" in d:
            d["metrics"] = [InferredMetric.from_dict(m) for m in d["metrics"]]
        if "automations" in d:
            d["automations"] = [InferredAutomation.from_dict(a) for a in d["automations"]]
        return cls(**d)


def _confidence_score(level: ConfidenceLevel) -> float:
    mapping = {
        ConfidenceLevel.HIGH: 0.92,
        ConfidenceLevel.MEDIUM: 0.72,
        ConfidenceLevel.LOW: 0.45,
        ConfidenceLevel.UNCERTAIN: 0.15,
    }
    return mapping.get(level, 0.5)