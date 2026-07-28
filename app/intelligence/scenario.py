"""
SHUNYA Explainable Intelligence — Scenario Provider

Demo scenarios are acceptable but must be isolated.
This module provides the Scenario Provider abstraction.

The runtime must never assume one industry.
Business logic remains universal.
Scenario packs only provide demonstration data.
Never allow demo assumptions to leak into the core architecture.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ScenarioObject:
    """A demonstration object within a scenario."""

    object_id: str
    name: str
    object_type: str
    space: str
    description: str
    health_class: str = "good"
    health_label: str = "Healthy"
    health_pct: float = 85.0
    metadata: dict = field(default_factory=dict)


@dataclass
class ScenarioEvent:
    """A demonstration event within a scenario."""

    event_id: str
    object_id: str
    event_type: str
    title: str
    description: str
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ScenarioEvidence:
    """A demonstration evidence item within a scenario."""

    evidence_id: str
    source: str
    title: str
    confidence: float = 0.85
    metadata: dict = field(default_factory=dict)


@dataclass
class ScenarioRelationship:
    """A demonstration relationship between objects."""

    source_id: str
    target_id: str
    relationship_type: str
    label: str


class ScenarioProvider(ABC):
    """Abstract base class for scenario data providers.

    Every scenario provider supplies demonstration data only.
    The core runtime never depends on any specific scenario.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this scenario (e.g. 'Investment Firm')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description of the scenario."""
        ...

    @abstractmethod
    def get_objects(self) -> list[ScenarioObject]:
        """Return demonstration objects for this scenario."""
        ...

    @abstractmethod
    def get_events(self) -> list[ScenarioEvent]:
        """Return demonstration events for this scenario."""
        ...

    @abstractmethod
    def get_evidence(self) -> list[ScenarioEvidence]:
        """Return demonstration evidence for this scenario."""
        ...

    @abstractmethod
    def get_relationships(self) -> list[ScenarioRelationship]:
        """Return demonstration relationships for this scenario."""
        ...


class InvestmentFirmScenario(ScenarioProvider):
    """Investment firm / private equity scenario.

    This is the default scenario used in the demo.
    """

    name = "Investment Firm"
    description = "A mid-market private equity firm with 24 portfolio companies"

    def get_objects(self) -> list[ScenarioObject]:
        return [
            ScenarioObject(
                object_id="jupiter-media",
                name="Jupiter Media Partnership",
                object_type="Agreement",
                space="Executive",
                description=(
                    "Strategic partnership agreement with Jupiter Media, a digital "
                    "publishing company with 4M monthly readers. Revenue share 60/40."
                ),
                health_class="good",
                health_label="Healthy",
                health_pct=85,
            ),
            ScenarioObject(
                object_id="northgate-mfg",
                name="Northgate Manufacturing",
                object_type="Portfolio Company",
                space="Portfolio",
                description=(
                    "Precision components manufacturer. 340 employees, two facilities. "
                    "Cash flow tightened due to rising raw material costs."
                ),
                health_class="caution",
                health_label="Needs attention",
                health_pct=62,
            ),
            ScenarioObject(
                object_id="q3-budget",
                name="Q3 Budget Allocation",
                object_type="Budget",
                space="Finance",
                description="Q3 engineering budget allocation. $1.2M. Pending approval.",
                health_class="good",
                health_label="Pending",
                health_pct=50,
            ),
            ScenarioObject(
                object_id="atlas-logistics",
                name="Atlas Logistics",
                object_type="Portfolio Company",
                space="Portfolio",
                description="Logistics provider. Revenue growing 9% QoQ. Margin improvement outpacing revenue growth.",
                health_class="good",
                health_label="Growing",
                health_pct=80,
            ),
            ScenarioObject(
                object_id="pine-street",
                name="Pine Street Partners",
                object_type="Portfolio Company",
                space="Portfolio",
                description="Real estate investment firm. Stable revenue. CFO transition in progress.",
                health_class="good",
                health_label="Stable",
                health_pct=75,
            ),
        ]

    def get_events(self) -> list[ScenarioEvent]:
        return [
            ScenarioEvent(
                event_id="evt-ju001",
                object_id="jupiter-media",
                event_type="decision",
                title="Agreement signed",
                description="Strategic partnership agreement fully executed",
                source="Legal",
                evidence_ids=["evid-ju001", "evid-ju002"],
            ),
            ScenarioEvent(
                event_id="evt-ju002",
                object_id="jupiter-media",
                event_type="change",
                title="Scope finalized",
                description="Scope finalized after negotiation. 3 regions, 18-month engagement.",
                source="Executive",
                evidence_ids=["evid-ju001"],
            ),
            ScenarioEvent(
                event_id="evt-nm001",
                object_id="northgate-mfg",
                event_type="risk",
                title="Cash flow alert",
                description="Covenant breach risk in 45 days at current burn rate",
                source="SHUNYA Intelligence",
                evidence_ids=["evid-nm001", "evid-nm002"],
            ),
            ScenarioEvent(
                event_id="evt-nm002",
                object_id="northgate-mfg",
                event_type="change",
                title="Aerospace contract delayed",
                description="Aerospace contract delayed 60 days, impacting cash flow projections",
                source="Operations",
                evidence_ids=["evid-nm002"],
            ),
            ScenarioEvent(
                event_id="evt-nm003",
                object_id="northgate-mfg",
                event_type="decision",
                title="New CFO appointed",
                description="New CFO appointed to address financial restructuring",
                source="Board",
                evidence_ids=["evid-nm003"],
            ),
        ]

    def get_evidence(self) -> list[ScenarioEvidence]:
        return [
            ScenarioEvidence(evidence_id="evid-ju001", source="Legal Review", title="Contract v2.4 — fully executed", confidence=0.95),
            ScenarioEvidence(evidence_id="evid-ju002", source="Compliance", title="Regulatory clearance — NA and EU", confidence=0.90),
            ScenarioEvidence(evidence_id="evid-nm001", source="SHUNYA Analysis", title="Cash flow analysis — 45 days to covenant breach", confidence=0.88),
            ScenarioEvidence(evidence_id="evid-nm002", source="Operations", title="Aerospace contract timeline update", confidence=0.75),
            ScenarioEvidence(evidence_id="evid-nm003", source="Board Minutes", title="CFO appointment resolution", confidence=0.95),
        ]

    def get_relationships(self) -> list[ScenarioRelationship]:
        return [
            ScenarioRelationship("jupiter-media", "q3-budget", "linked", "Q3 budget allocation"),
            ScenarioRelationship("northgate-mfg", "q3-budget", "linked", "Covenant tracker"),
            ScenarioRelationship("jupiter-media", "atlas-logistics", "reference", "Peer portfolio company"),
            ScenarioRelationship("northgate-mfg", "pine-street", "reference", "Peer portfolio company"),
        ]


# ─── Registry ───

_registry: dict[str, type[ScenarioProvider]] = {}


def register(provider_class: type[ScenarioProvider]) -> type[ScenarioProvider]:
    """Register a scenario provider class."""
    instance = provider_class()
    _registry[instance.name] = provider_class
    return provider_class


def get_scenario(name: str) -> Optional[ScenarioProvider]:
    """Get a scenario provider by name."""
    cls = _registry.get(name)
    if cls:
        return cls()
    return None


def list_scenarios() -> list[dict]:
    """List all registered scenarios."""
    return [
        {"name": cls().name, "description": cls().description}
        for cls in _registry.values()
    ]


# Register the default scenario
register(InvestmentFirmScenario)