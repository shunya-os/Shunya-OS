"""Universal Asset Intelligence — Core Engine.

Pure computation engine for asset analysis:
ownership reasoning, lifecycle reasoning, utilization analysis,
dependency analysis, maintenance prediction, health scoring,
risk scoring, valuation, anomaly detection, duplicate detection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.asset_intelligence.models import (
    Asset,
    AssetRecommendation,
    AssetStatus,
    AssetType,
    HealthStatus,
    RiskLevel,
    _generate_id,
    _now_iso,
)


class AssetIntelligenceEngine:
    """Pure computation engine for Universal Asset Intelligence."""

    # ── Ownership Reasoning ─────────────────────────────────────────────

    def reason_about_ownership(self, asset: Asset) -> dict[str, Any]:
        if not asset.owner_id:
            return {"has_owner": False, "risk": "high", "recommendation": "Assign an owner immediately"}
        return {"has_owner": True, "owner_id": asset.owner_id, "risk": "low",
                "has_custodian": bool(asset.custodian_id)}

    # ── Lifecycle Reasoning ─────────────────────────────────────────────

    def reason_about_lifecycle(self, asset: Asset) -> list[AssetRecommendation]:
        recs: list[AssetRecommendation] = []
        if asset.is_disposed:
            return recs

        days_since_maint = asset.days_since_maintenance
        if days_since_maint > 365:
            recs.append(AssetRecommendation(
                title=f"Maintenance overdue for '{asset.name}'",
                description=f"No maintenance recorded in {days_since_maint} days",
                priority="high", reasoning=f"Asset has not been maintained in {days_since_maint} days",
                confidence=0.8,
                affected_assets=[asset.asset_id],
                expected_impact="Reduced asset lifespan and reliability",
                evidence=[{"type": "days_since_maintenance", "value": days_since_maint}],
            ))
        elif days_since_maint > 180:
            recs.append(AssetRecommendation(
                title=f"Maintenance recommended for '{asset.name}'",
                description=f"Last maintenance was {days_since_maint} days ago",
                priority="medium", reasoning="Routine maintenance interval exceeded",
                confidence=0.6,
                affected_assets=[asset.asset_id],
                expected_impact="Maintains optimal asset performance",
                evidence=[{"type": "days_since_maintenance", "value": days_since_maint}],
            ))

        if asset.health_score < 0.3:
            recs.append(AssetRecommendation(
                title=f"'{asset.name}' health critical — consider replacement",
                description=f"Health score {asset.health_score} indicates end of life",
                priority="high", reasoning="Asset health critically low",
                confidence=0.85,
                affected_assets=[asset.asset_id],
                expected_impact="Prevents failure-related disruptions",
                evidence=[{"type": "health_score", "value": asset.health_score}],
            ))

        return recs

    # ── Utilization Analysis ────────────────────────────────────────────

    def analyze_utilization(self, asset: Asset) -> dict[str, Any]:
        if asset.utilization < 0.2:
            return {"level": "underutilized", "score": asset.utilization,
                    "recommendation": "Consider consolidation or decommissioning",
                    "evidence": [{"type": "utilization", "value": asset.utilization}]}
        elif asset.utilization > 0.9:
            return {"level": "overutilized", "score": asset.utilization,
                    "recommendation": "Consider adding capacity or replacing with higher-capacity asset",
                    "evidence": [{"type": "utilization", "value": asset.utilization}]}
        return {"level": "optimal", "score": asset.utilization,
                "recommendation": "Utilization is within healthy range",
                "evidence": [{"type": "utilization", "value": asset.utilization}]}

    # ── Dependency Analysis ─────────────────────────────────────────────

    def analyze_dependencies(self, assets: list[Asset]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        asset_map = {a.asset_id: a for a in assets}

        for asset in assets:
            for dep_id in asset.dependencies:
                if dep_id not in asset_map:
                    issues.append({
                        "type": "missing_dependency",
                        "asset_id": asset.asset_id,
                        "asset_name": asset.name,
                        "missing_dependency": dep_id,
                        "severity": "high",
                        "evidence": [{"type": "dependency_not_found", "value": dep_id}],
                    })
                else:
                    dep = asset_map[dep_id]
                    if dep.is_disposed:
                        issues.append({
                            "type": "disposed_dependency",
                            "asset_id": asset.asset_id,
                            "asset_name": asset.name,
                            "dependency_name": dep.name,
                            "severity": "critical",
                            "evidence": [{"type": "dependency_disposed", "value": dep.name}],
                        })

        return issues

    # ── Maintenance Prediction ───────────────────────────────────────────

    def predict_maintenance(self, asset: Asset) -> AssetRecommendation | None:
        days_since_maint = asset.days_since_maintenance
        if days_since_maint > 365:
            return AssetRecommendation(
                title=f"Critical maintenance needed: {asset.name}",
                description=f"{days_since_maint} days since last maintenance",
                priority="critical", reasoning="Maintenance interval severely exceeded",
                confidence=0.9,
                affected_assets=[asset.asset_id],
                expected_impact="Prevents asset failure",
                evidence=[{"type": "days_since_maintenance", "value": days_since_maint}],
            )
        next_due_days = 180 - days_since_maint
        if next_due_days < 30:
            return AssetRecommendation(
                title=f"Maintenance due soon: {asset.name}",
                description=f"Next maintenance in {max(0, next_due_days)} days",
                priority="high" if next_due_days < 7 else "medium",
                reasoning="Routine maintenance approaching",
                confidence=0.7,
                affected_assets=[asset.asset_id],
                expected_impact="Maintains asset reliability",
                evidence=[{"type": "days_until_maintenance_due", "value": max(0, next_due_days)}],
            )
        return None

    # ── Health Scoring ──────────────────────────────────────────────────

    def compute_health(self, asset: Asset) -> dict[str, Any]:
        score = 0.5
        if asset.maintenance:
            score += 0.2
        days_since = asset.days_since_maintenance
        if days_since < 30:
            score += 0.2
        elif days_since < 180:
            score += 0.1
        elif days_since > 365:
            score -= 0.2
        if asset.utilization > 0 and asset.utilization < 0.9:
            score += 0.1
        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            level = HealthStatus.EXCELLENT.value
        elif score >= 0.6:
            level = HealthStatus.GOOD.value
        elif score >= 0.4:
            level = HealthStatus.FAIR.value
        elif score >= 0.2:
            level = HealthStatus.POOR.value
        else:
            level = HealthStatus.CRITICAL.value

        return {"score": round(score, 4), "level": level,
                "factors": {"has_maintenance": bool(asset.maintenance),
                            "days_since_maintenance": days_since,
                            "utilization": asset.utilization}}

    # ── Risk Scoring ────────────────────────────────────────────────────

    def score_risks(self, assets: list[Asset]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for asset in assets:
            risk_score = 0.0
            if not asset.owner_id:
                risk_score += 0.3
            if asset.health_score < 0.4:
                risk_score += 0.3
            if asset.days_since_maintenance > 365:
                risk_score += 0.3
            if asset.utilization > 0.95:
                risk_score += 0.2
            if risk_score > 0:
                level = "critical" if risk_score > 0.8 else "high" if risk_score > 0.5 else "medium"
                risks.append({
                    "asset_id": asset.asset_id, "asset_name": asset.name,
                    "risk_score": round(risk_score, 2), "level": level,
                    "factors": {"no_owner": not bool(asset.owner_id),
                                "low_health": asset.health_score < 0.4,
                                "maintenance_overdue": asset.days_since_maintenance > 365,
                                "overutilized": asset.utilization > 0.95},
                })
        return risks

    # ── Financial Valuation ─────────────────────────────────────────────

    def estimate_financial_value(self, asset: Asset, category_avg_value: float = 0.0) -> dict[str, Any]:
        base = asset.financial_value or category_avg_value
        depreciation = 0.0
        if asset.health_score < 0.3:
            depreciation = 0.5
        elif asset.health_score < 0.6:
            depreciation = 0.25
        elif asset.days_since_maintenance > 365:
            depreciation = 0.15

        estimated = base * (1 - depreciation)
        return {
            "current_value": round(estimated, 2),
            "depreciation_pct": round(depreciation * 100, 1),
            "factors": {"health_depreciation": depreciation},
        }

    # ── Anomaly Detection ───────────────────────────────────────────────

    def detect_anomalies(self, assets: list[Asset]) -> list[AssetRecommendation]:
        recs: list[AssetRecommendation] = []
        asset_map = {a.asset_id: a for a in assets}

        for asset in assets:
            if asset.health_score < 0.2 and asset.is_active:
                recs.append(AssetRecommendation(
                    title=f"Anomaly: '{asset.name}' active but critically unhealthy",
                    description=f"Health is {asset.health_score} but asset is active",
                    priority="critical", reasoning="Active asset with critically low health",
                    confidence=0.9,
                    affected_assets=[asset.asset_id],
                    expected_impact="Risk of unexpected failure",
                    evidence=[{"type": "health_score", "value": asset.health_score},
                              {"type": "status", "value": asset.status}],
                ))

            if asset.utilization < 0.05 and asset.is_active:
                recs.append(AssetRecommendation(
                    title=f"'{asset.name}' has near-zero utilization",
                    description=f"Utilization is {asset.utilization:.0%} — consider decommissioning",
                    priority="medium", reasoning="Asset is active but barely used",
                    confidence=0.8,
                    affected_assets=[asset.asset_id],
                    expected_impact="Cost savings from decommissioning",
                    evidence=[{"type": "utilization", "value": asset.utilization}],
                ))

        # Duplicate detection
        for i, a in enumerate(assets):
            for b in assets[i + 1:]:
                if a.name.lower() == b.name.lower():
                    recs.append(AssetRecommendation(
                        title=f"Potential duplicate: '{a.name}'",
                        description=f"Two assets share the name '{a.name}'",
                        priority="medium", reasoning="Duplicate asset names found",
                        confidence=0.6,
                        affected_assets=[a.asset_id, b.asset_id],
                        expected_impact="Resolve duplication",
                        evidence=[{"type": "duplicate_name", "value": a.name}],
                    ))

        return recs

    # ── Explainable Recommendation ──────────────────────────────────────

    def explain_recommendation(self, rec: AssetRecommendation) -> dict[str, Any]:
        return {
            "recommendation": rec.title,
            "description": rec.description,
            "reasoning": rec.reasoning,
            "confidence": rec.confidence,
            "affected_assets": rec.affected_assets,
            "expected_impact": rec.expected_impact,
            "evidence": rec.evidence,
            "explanation": "This recommendation is based on the following evidence:",
            "evidence_summary": [{"basis": e.get("type", ""), "value": e.get("value", "")} for e in rec.evidence],
        }

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, profile) -> dict[str, Any]:
        active = [a for a in profile.assets if a.is_active]
        return {
            "asset_count": len(profile.assets),
            "active_count": len(active),
            "total_value": profile.total_value,
            "categories": list(set(a.category for a in profile.assets)),
            "health_distribution": {
                "excellent": sum(1 for a in active if a.health == "excellent"),
                "good": sum(1 for a in active if a.health == "good"),
                "fair": sum(1 for a in active if a.health == "fair"),
                "poor": sum(1 for a in active if a.health == "poor"),
                "critical": sum(1 for a in active if a.health == "critical"),
            },
            "risks": self.score_risks(active),
        }