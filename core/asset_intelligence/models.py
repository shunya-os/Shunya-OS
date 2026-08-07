"""Universal Asset Intelligence — Data Models.

Asset Intelligence models every identifiable entity that exists through time
and participates in human or organizational reality.

It does not model inventory software, fixed asset accounting, or IT asset management.
It models Assets.

UCP-07 — Universal Asset Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.journey_semantics import apply_transition as _apply_transition, validate_transition as _validate_transition


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


class AssetCategory(str, Enum):
    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    ELECTRONICS = "electronics"
    IDENTITY_DOCUMENT = "identity_document"
    DIGITAL = "digital"
    FINANCIAL = "financial"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CERTIFICATE = "certificate"
    INFRASTRUCTURE = "infrastructure"
    MANUFACTURING = "manufacturing"
    INVENTORY = "inventory"
    TRAVEL = "travel"
    WEARABLE = "wearable"
    MEDICAL = "medical"
    OFFICE_EQUIPMENT = "office_equipment"
    SOFTWARE = "software"
    API = "api"
    WALLET = "wallet"
    BADGE = "badge"
    RESERVATION = "reservation"
    MEMBERSHIP = "membership"
    OTHER = "other"


class AssetType(str, Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    VEHICLE_CAR = "vehicle_car"
    VEHICLE_BIKE = "vehicle_bike"
    PASSPORT = "passport"
    LAPTOP = "laptop"
    MOBILE_PHONE = "mobile_phone"
    SERVER = "server"
    DOMAIN_NAME = "domain_name"
    SOFTWARE_LICENSE = "software_license"
    API_KEY = "api_key"
    BANK_ACCOUNT = "bank_account"
    INVESTMENT_PORTFOLIO = "investment_portfolio"
    CAMERA = "camera"
    MEDICAL_DEVICE = "medical_device"
    MANUFACTURING_MACHINE = "manufacturing_machine"
    INVENTORY_ITEM = "inventory_item"
    FLIGHT_TICKET = "flight_ticket"
    HOTEL_RESERVATION = "hotel_reservation"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    EMPLOYEE_BADGE = "employee_badge"
    CERTIFICATE = "certificate"
    DIGITAL_WALLET = "digital_wallet"
    OTHER = "other"


class AssetStatus(str, Enum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    VERIFIED = "verified"
    ACTIVE = "active"
    MAINTAINED = "maintained"
    MODIFIED = "modified"
    TRANSFERRED = "transferred"
    ARCHIVED = "archived"
    DISPOSED = "disposed"
    RECOVERED = "recovered"

    @classmethod
    def valid_transitions(cls) -> dict[str, list[str]]:
        return {
            "discovered": ["registered", "archived"],
            "registered": ["verified", "archived"],
            "verified": ["active", "archived"],
            "active": ["maintained", "modified", "transferred", "archived", "disposed"],
            "maintained": ["active", "modified", "archived"],
            "modified": ["active", "verified", "archived"],
            "transferred": ["active", "verified", "archived", "disposed"],
            "archived": ["disposed", "recovered"],
            "disposed": [],
            "recovered": ["active", "verified"],
        }

    @classmethod
    def is_valid_transition(cls, current: str, target: str) -> bool:
        return _validate_transition(current, target, cls.valid_transitions())


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthStatus(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class AssetLocation:
    location_id: str = field(default_factory=_generate_id)
    name: str = ""
    address: str = ""
    coordinates: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"location_id": self.location_id, "name": self.name,
                "address": self.address, "coordinates": dict(self.coordinates),
                "metadata": dict(self.metadata)}


@dataclass
class MaintenanceRecord:
    record_id: str = field(default_factory=_generate_id)
    date: str = ""
    description: str = ""
    cost: float = 0.0
    performed_by: str = ""
    next_due: str = ""
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"record_id": self.record_id, "date": self.date,
                "description": self.description, "cost": self.cost,
                "performed_by": self.performed_by, "next_due": self.next_due,
                "evidence_ids": list(self.evidence_ids)}


@dataclass
class AssetEvent:
    event_id: str = field(default_factory=_generate_id)
    event_type: str = ""
    description: str = ""
    timestamp: str = field(default_factory=_now_iso)
    actor: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "event_type": self.event_type,
                "description": self.description, "timestamp": self.timestamp,
                "actor": self.actor, "metadata": dict(self.metadata)}


@dataclass
class Asset:
    asset_id: str = field(default_factory=_generate_id)
    category: str = AssetCategory.OTHER.value
    asset_type: str = AssetType.OTHER.value
    status: str = AssetStatus.DISCOVERED.value
    name: str = ""
    description: str = ""
    owner_id: str = ""
    custodian_id: str = ""
    location: AssetLocation | None = None
    lifecycle_state: str = AssetStatus.DISCOVERED.value
    relationships: list[str] = field(default_factory=list)
    financial_value: float = 0.0
    financial_value_currency: str = "INR"
    operational_value: float = 0.5
    health: str = HealthStatus.UNKNOWN.value
    health_score: float = 0.5
    utilization: float = 0.5
    maintenance: list[MaintenanceRecord] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    agreement_ids: list[str] = field(default_factory=list)
    communications: list[str] = field(default_factory=list)
    journey_ids: list[str] = field(default_factory=list)
    events: list[AssetEvent] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_active(self) -> bool:
        return self.status in (AssetStatus.ACTIVE.value, AssetStatus.MAINTAINED.value,
                                AssetStatus.MODIFIED.value, AssetStatus.VERIFIED.value)

    @property
    def is_disposed(self) -> bool:
        return self.status == AssetStatus.DISPOSED.value

    def transition_to(self, new_status: str) -> bool:
        success, _ = _apply_transition(
            self.status, new_status,
            AssetStatus.valid_transitions(),
            on_transition=lambda curr, tgt: setattr(self, 'updated_at', _now_iso()) or
                self.events.append(AssetEvent(
                    event_type="status_change",
                    description=f"Status changed from {curr} to {tgt}",
                ))
        )
        if success:
            self.status = new_status
        return success

    @property
    def days_since_maintenance(self) -> int:
        if not self.maintenance:
            return 999
        from datetime import datetime, timezone
        latest = max(self.maintenance, key=lambda m: m.date)
        try:
            dt = datetime.fromisoformat(latest.date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).days
        except (ValueError, TypeError):
            return 999

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id, "category": self.category,
            "asset_type": self.asset_type, "status": self.status,
            "name": self.name, "description": self.description,
            "owner_id": self.owner_id, "custodian_id": self.custodian_id,
            "location": self.location.to_dict() if self.location else None,
            "lifecycle_state": self.lifecycle_state,
            "relationships": list(self.relationships),
            "financial_value": self.financial_value,
            "financial_value_currency": self.financial_value_currency,
            "operational_value": self.operational_value,
            "health": self.health, "health_score": self.health_score,
            "utilization": self.utilization,
            "maintenance": [m.to_dict() for m in self.maintenance],
            "dependencies": list(self.dependencies),
            "tags": list(self.tags), "knowledge_ids": list(self.knowledge_ids),
            "document_ids": list(self.document_ids),
            "agreement_ids": list(self.agreement_ids),
            "journey_ids": list(self.journey_ids),
            "evidence_ids": list(self.evidence_ids),
            "risks": list(self.risks),
            "metadata": dict(self.metadata),
            "created_at": self.created_at, "updated_at": self.updated_at,
            "is_active": self.is_active, "is_disposed": self.is_disposed,
            "days_since_maintenance": self.days_since_maintenance,
        }


@dataclass
class AssetProfile:
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    assets: list[Asset] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_assets(self) -> int:
        return len(self.assets)
    @property
    def active_assets(self) -> list[Asset]:
        return [a for a in self.assets if a.is_active]
    @property
    def total_value(self) -> float:
        return sum(a.financial_value for a in self.assets)

    def to_dict(self) -> dict[str, Any]:
        return {"profile_id": self.profile_id, "owner_id": self.owner_id,
                "label": self.label, "total_assets": self.total_assets,
                "active_count": len(self.active_assets),
                "total_value": self.total_value,
                "metadata": dict(self.metadata),
                "created_at": self.created_at, "updated_at": self.updated_at}


@dataclass
class AssetRecommendation:
    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reasoning: str = ""
    confidence: float = 0.0
    affected_assets: list[str] = field(default_factory=list)
    expected_impact: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {"rec_id": self.rec_id, "title": self.title,
                "description": self.description, "priority": self.priority,
                "reasoning": self.reasoning, "confidence": self.confidence,
                "affected_assets": list(self.affected_assets),
                "expected_impact": self.expected_impact,
                "evidence": list(self.evidence),
                "metadata": dict(self.metadata),
                "generated_at": self.generated_at}