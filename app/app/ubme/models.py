"""Universal Business Model Engine — Canonical Metadata Models.

Everything in UBME is metadata. No business-specific models exist here.
This module defines the data types that describe ANY business domain.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# ── Field Types ───────────────────────────────────────────────────────────

class FieldType(str, enum.Enum):
    """All supported field types — adding one extends the platform, not business code."""
    TEXT = "text"
    INTEGER = "integer"
    LONG_TEXT = "long_text"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    DURATION = "duration"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    ADDRESS = "address"
    LOCATION = "location"
    PERSON = "person"
    ORGANIZATION = "organization"
    ATTACHMENT = "attachment"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    JSON = "json"
    AI_GENERATED = "ai_generated"
    COMPUTED = "computed"
    FORMULA = "formula"
    LOOKUP = "lookup"
    RELATIONSHIP = "relationship"
    COLLECTION = "collection"
    SELECT = "select"


class RelationshipType(str, enum.Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    HIERARCHICAL = "hierarchical"
    GRAPH = "graph"
    POLYMORPHIC = "polymorphic"
    BIDIRECTIONAL = "bidirectional"


class ViewType(str, enum.Enum):
    LIST = "list"
    TABLE = "table"
    KANBAN = "kanban"
    CALENDAR = "calendar"
    TIMELINE = "timeline"
    GALLERY = "gallery"
    MAP = "map"
    HIERARCHY = "hierarchy"
    DASHBOARD = "dashboard"
    DETAIL = "detail"
    BOARD = "board"
    ANALYTICS = "analytics"


class WorkflowStateType(str, enum.Enum):
    INITIAL = "initial"
    INTERMEDIATE = "intermediate"
    FINAL = "final"


# ── Metadata Models ──────────────────────────────────────────────────────


@dataclass
class FieldDef:
    """Definition of a single field on an object type."""
    key: str
    label: str
    field_type: FieldType = FieldType.TEXT
    required: bool = False
    unique: bool = False
    default: Any = None
    options: list[str] | None = None
    placeholder: str = ""
    help_text: str = ""
    validation: dict | None = None
    ai_generated: bool = False
    computed_formula: str = ""
    relationship_type: str = ""
    target_object_type: str = ""
    display_in_list: bool = True
    searchable: bool = True
    order: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["field_type"] = self.field_type.value
        if self.options is not None:
            d["options"] = self.options
        if self.validation is not None:
            d["validation"] = self.validation
        return d

    @classmethod
    def from_dict(cls, d: dict) -> FieldDef:
        d = dict(d)
        d["field_type"] = FieldType(d["field_type"]) if isinstance(d.get("field_type"), str) else d.get("field_type", FieldType.TEXT)
        return cls(**d)


@dataclass
class ObjectTypeDef:
    """Definition of an object type — the core unit of a business module."""
    key: str
    name: str
    plural_name: str = ""
    description: str = ""
    icon: str = "📦"
    color: str = "#6366f1"
    category: str = "business"
    fields: list[FieldDef] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    lifecycle: list[str] | None = None
    ownership: str = "organization"
    searchable: bool = True
    ai_semantics: dict | None = None
    default_view: str = "list"
    group_by_field: str = ""
    calendar_field: str = ""
    map_field: str = ""
    actions: list[ActionDef] = field(default_factory=list)

    def __post_init__(self):
        if not self.plural_name:
            self.plural_name = self.name + "s"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["fields"] = [f.to_dict() for f in (self.fields or [])]
        if self.ai_semantics:
            d["ai_semantics"] = self.ai_semantics
        if self.lifecycle:
            d["lifecycle"] = self.lifecycle
        if self.actions:
            d["actions"] = [a.to_dict() for a in self.actions]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> ObjectTypeDef:
        d = dict(d)
        if "fields" in d:
            d["fields"] = [FieldDef.from_dict(f) for f in d["fields"]]
        if "actions" in d:
            d["actions"] = [ActionDef.from_dict(a) for a in d["actions"]]
        return cls(**d)


@dataclass
class ViewDef:
    """A view configuration for rendering objects of a given type."""
    key: str
    label: str
    view_type: ViewType = ViewType.LIST
    object_type: str = ""
    fields: list[str] = field(default_factory=list)
    filters: dict | None = None
    sort_by: str = ""
    group_by: str = ""
    is_default: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["view_type"] = self.view_type.value
        if self.filters:
            d["filters"] = self.filters
        return d

    @classmethod
    def from_dict(cls, d: dict) -> ViewDef:
        d = dict(d)
        d["view_type"] = ViewType(d["view_type"]) if isinstance(d.get("view_type"), str) else d.get("view_type", ViewType.LIST)
        return cls(**d)


@dataclass
class WorkflowStateDef:
    """A state in a workflow."""
    key: str
    label: str
    state_type: WorkflowStateType = WorkflowStateType.INTERMEDIATE

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state_type"] = self.state_type.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowStateDef:
        d = dict(d)
        d["state_type"] = WorkflowStateType(d["state_type"]) if isinstance(d.get("state_type"), str) else d.get("state_type", WorkflowStateType.INTERMEDIATE)
        return cls(**d)


@dataclass
class WorkflowTransitionDef:
    """A transition between workflow states."""
    from_state: str
    to_state: str
    label: str = ""
    requires_approval: bool = False
    condition: str = ""
    trigger: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowTransitionDef:
        return cls(**d)


@dataclass
class WorkflowDef:
    """A workflow definition for an object type."""
    key: str
    name: str
    object_type: str
    states: list[WorkflowStateDef] = field(default_factory=list)
    transitions: list[WorkflowTransitionDef] = field(default_factory=list)
    default_state: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["states"] = [s.to_dict() for s in (self.states or [])]
        d["transitions"] = [t.to_dict() for t in (self.transitions or [])]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowDef:
        d = dict(d)
        if "states" in d:
            d["states"] = [WorkflowStateDef.from_dict(s) for s in d["states"]]
        if "transitions" in d:
            d["transitions"] = [WorkflowTransitionDef.from_dict(t) for t in d["transitions"]]
        return cls(**d)


@dataclass
class NavigationEntry:
    """A navigation entry for a module."""
    label: str
    object_type: str
    icon: str = ""
    view_key: str = "default"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> NavigationEntry:
        return cls(**d)


@dataclass
class ActionDef:
    """An action an object type advertises."""
    key: str
    label: str
    icon: str = ""
    endpoint: str = ""
    method: str = "POST"
    requires_confirmation: bool = False
    requires_approval: bool = False
    available_when: str = ""  # status condition, e.g. "status == 'draft'"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> ActionDef:
        return cls(**d)


@dataclass
class DashboardCard:
    """A card on the module dashboard."""
    key: str
    label: str
    card_type: str  # count | sum | recent | chart | alert
    object_type: str = ""
    field: str = ""
    filter_criteria: str = ""
    icon: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> DashboardCard:
        return cls(**d)


@dataclass
class ModuleDef:
    """Complete definition of a business module."""
    key: str
    name: str
    description: str = ""
    icon: str = "🏢"
    color: str = "#6366f1"
    navigation: list[NavigationEntry] = field(default_factory=list)
    object_types: list[ObjectTypeDef] = field(default_factory=list)
    views: list[ViewDef] = field(default_factory=list)
    workflows: list[WorkflowDef] = field(default_factory=list)
    dashboard_config: dict | None = None
    dashboard_cards: list[DashboardCard] = field(default_factory=list)
    template_source: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        d = asdict(self)
        d["navigation"] = [n.to_dict() for n in (self.navigation or [])]
        d["object_types"] = [ot.to_dict() for ot in (self.object_types or [])]
        d["views"] = [v.to_dict() for v in (self.views or [])]
        d["workflows"] = [w.to_dict() for w in (self.workflows or [])]
        if self.dashboard_config:
            d["dashboard_config"] = self.dashboard_config
        if self.dashboard_cards:
            d["dashboard_cards"] = [c.to_dict() for c in self.dashboard_cards]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> ModuleDef:
        d = dict(d)
        if "navigation" in d:
            d["navigation"] = [NavigationEntry.from_dict(n) for n in d["navigation"]]
        if "object_types" in d:
            d["object_types"] = [ObjectTypeDef.from_dict(ot) for ot in d["object_types"]]
        if "views" in d:
            d["views"] = [ViewDef.from_dict(v) for v in d["views"]]
        if "workflows" in d:
            d["workflows"] = [WorkflowDef.from_dict(w) for w in d["workflows"]]
        if "dashboard_cards" in d:
            d["dashboard_cards"] = [DashboardCard.from_dict(c) for c in d["dashboard_cards"]]
        return cls(**d)


@dataclass
class BusinessTemplate:
    """Pre-configured business module template."""
    id: str
    name: str
    description: str
    icon: str
    industry: str
    module: ModuleDef

    def to_dict(self) -> dict:
        d = asdict(self)
        d["module"] = self.module.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> BusinessTemplate:
        d = dict(d)
        if "module" in d:
            d["module"] = ModuleDef.from_dict(d["module"])
        return cls(**d)