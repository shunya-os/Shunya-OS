"""Universal Asset Intelligence — Runtime.

AssetIntelligenceRuntime composes from all frozen UCPs.
No Inventory Runtime. No Asset Management Runtime. No CMDB Runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from core.asset_intelligence.engine import AssetIntelligenceEngine
from core.asset_intelligence.models import (
    Asset,
    AssetLocation,
    AssetProfile,
    AssetRecommendation,
    AssetStatus,
    AssetType,
    HealthStatus,
    MaintenanceRecord,
    RiskLevel,
    _generate_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


class AssetIntelligenceRuntime:
    """Universal Asset Intelligence — single capability runtime."""

    def __init__(self) -> None:
        self._engine = AssetIntelligenceEngine()
        self._profiles: dict[str, AssetProfile] = {}
        self._reality_listeners: list[Callable[[dict[str, Any]], None]] = []

    def get_or_create_profile(self, owner_id: str, label: str = "") -> AssetProfile:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        profile = AssetProfile(owner_id=owner_id, label=label or f"Asset profile for {owner_id}")
        self._profiles[profile.profile_id] = profile
        return profile

    def get_profile(self, pid: str) -> AssetProfile | None:
        return self._profiles.get(pid)

    # Simplified: owner_id is the key
    def _resolve(self, owner_id: str) -> AssetProfile | None:
        for p in self._profiles.values():
            if p.owner_id == owner_id:
                return p
        return None

    # ── Asset CRUD ──────────────────────────────────────────────────────

    def register_asset(
        self, owner_id: str,
        category: str = "other", asset_type: str = "other",
        name: str = "", description: str = "",
        owner: str = "", custodian: str = "",
        financial_value: float = 0.0, currency: str = "INR",
        tags: list[str] | None = None, location_name: str = "",
    ) -> Asset | None:
        profile = self._resolve(owner_id)
        if not profile:
            profile = self.get_or_create_profile(owner_id)
        profile = self._resolve(owner_id)
        if not profile:
            return None

        asset = Asset(
            category=category, asset_type=asset_type,
            name=name, description=description,
            owner_id=owner, custodian_id=custodian,
            financial_value=financial_value,
            financial_value_currency=currency,
            tags=tags or [],
            location=AssetLocation(name=location_name) if location_name else None,
            status=AssetStatus.DISCOVERED.value,
        )
        asset.health_score = self._engine.compute_health(asset)["score"]
        asset.health = self._engine.compute_health(asset)["level"]
        profile.assets.append(asset)
        profile.updated_at = _now_iso()
        return asset

    def get_asset(self, owner_id: str, asset_id: str) -> Asset | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        for a in profile.assets:
            if a.asset_id == asset_id:
                return a
        return None

    def transition_status(self, owner_id: str, asset_id: str, new_status: str) -> bool:
        asset = self.get_asset(owner_id, asset_id)
        if not asset:
            return False
        return asset.transition_to(new_status)

    # ── Intelligence ────────────────────────────────────────────────────

    def analyze_asset(self, owner_id: str, asset_id: str) -> dict[str, Any] | None:
        asset = self.get_asset(owner_id, asset_id)
        if not asset:
            return None
        return {
            "asset": asset.to_dict(),
            "ownership": self._engine.reason_about_ownership(asset),
            "lifecycle": [r.to_dict() for r in self._engine.reason_about_lifecycle(asset)],
            "utilization": self._engine.analyze_utilization(asset),
            "health": self._engine.compute_health(asset),
            "financial": self._engine.estimate_financial_value(asset),
        }

    def analyze_all(self, owner_id: str) -> dict[str, Any] | None:
        profile = self._resolve(owner_id)
        if not profile:
            return None
        deps = self._engine.analyze_dependencies(profile.assets)
        risks = self._engine.score_risks(profile.assets)
        anomalies = [r.to_dict() for r in self._engine.detect_anomalies(profile.assets)]
        return {
            "total_assets": profile.total_assets,
            "active_count": len(profile.active_assets),
            "total_value": profile.total_value,
            "dependencies": deps,
            "risks": risks,
            "anomalies": anomalies,
        }

    def get_recommendations(self, owner_id: str, asset_id: str) -> list[dict[str, Any]]:
        asset = self.get_asset(owner_id, asset_id)
        if not asset:
            return []
        recs: list[AssetRecommendation] = []
        recs.extend(self._engine.reason_about_lifecycle(asset))
        maint = self._engine.predict_maintenance(asset)
        if maint:
            recs.append(maint)
        return [r.to_dict() for r in recs]

    def add_maintenance(self, owner_id: str, asset_id: str,
                         date: str, description: str, cost: float = 0.0) -> bool:
        asset = self.get_asset(owner_id, asset_id)
        if not asset:
            return False
        asset.maintenance.append(MaintenanceRecord(date=date, description=description, cost=cost))
        asset.health_score = self._engine.compute_health(asset)["score"]
        asset.health = self._engine.compute_health(asset)["level"]
        asset.updated_at = _now_iso()
        return True

    # ── Lifecycle ───────────────────────────────────────────────────────

    def initialize(self) -> None:
        logger.info("AssetIntelligenceRuntime initialized")
    def shutdown(self) -> None:
        self._profiles.clear()
        self._reality_listeners.clear()
    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "runtime": "asset_intelligence", "profile_count": len(self._profiles)}
    def handle_event(self, event: Any) -> None:
        if isinstance(event, dict):
            self.notify(event)
    def get_capabilities(self) -> list[str]:
        return ["asset.profile", "asset.register", "asset.analyze", "asset.health",
                "asset.utilization", "asset.maintenance", "asset.risks", "asset.reality_integration"]

    def notify(self, notification: dict[str, Any]) -> None:
        pass  # Placeholder for Reality integration

    def register_execution_actions(self, execution_runtime: Any) -> None:
        try:
            from core.execution_runtime.models import ActionContract
        except ImportError:
            return
        execution_runtime.register_action("asset.analyze", ActionContract(
            action_id="asset.analyze", description="Analyze an asset",
            input_schema={"type": "object", "properties": {
                "owner_id": {"type": "string"}, "asset_id": {"type": "string"},
            }, "required": ["owner_id", "asset_id"]},
            output_schema={"type": "object"},
        ), handler=self.analyze_asset)

    def _notify(self, n: dict) -> None:
        for l in self._reality_listeners:
            try:
                l(n)
            except Exception:
                pass
    def register_reality_listener(self, l: Callable) -> None:
        self._reality_listeners.append(l)
    def unregister_reality_listener(self, l: Callable) -> None:
        if l in self._reality_listeners:
            self._reality_listeners.remove(l)