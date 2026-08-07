"""Universal Agreement Intelligence — Core Engine.

Pure computation engine for agreement analysis:
obligation discovery, fulfilment monitoring, breach detection,
dependency analysis, amendment reasoning, renewal recommendations,
expiry prediction, compliance reasoning, risk scoring, trust impact.
"""

from __future__ import annotations

from typing import Any

from core.agreement_intelligence.models import (
    Agreement,
    AgreementRecommendation,
    AgreementStatus,
    Obligation,
    ObligationStatus,
    RiskLevel,
    _generate_id,
    _now_iso,
)


class AgreementIntelligenceEngine:
    """Pure computation engine for Universal Agreement Intelligence."""

    # ── Obligation Discovery ────────────────────────────────────────────

    def discover_obligations(self, agreement: Agreement) -> list[dict[str, Any]]:
        """Discover obligations from agreement content."""
        discovered: list[dict[str, Any]] = []

        for party in agreement.parties:
            for obligation in agreement.obligations:
                if obligation.party_id == party.party_id:
                    discovered.append({
                        "party": party.name,
                        "party_role": party.role,
                        "obligation": obligation.description,
                        "status": obligation.status,
                        "due_date": obligation.due_date,
                    })
        return discovered

    # ── Fulfilment Monitoring ───────────────────────────────────────────

    def monitor_fulfilment(self, agreement: Agreement) -> dict[str, Any]:
        """Monitor fulfilment status across all obligations."""
        total = len(agreement.obligations)
        if total == 0:
            return {"fulfilment_pct": 0, "status": "no_obligations", "by_party": {}}

        fulfilled = sum(1 for o in agreement.obligations if o.status == ObligationStatus.FULFILLED.value)
        breached = sum(1 for o in agreement.obligations if o.status == ObligationStatus.BREACHED.value)
        pending = total - fulfilled - breached

        by_party: dict[str, dict[str, int]] = {}
        for o in agreement.obligations:
            party = o.party_id
            if party not in by_party:
                by_party[party] = {"total": 0, "fulfilled": 0, "breached": 0, "pending": 0}
            by_party[party]["total"] += 1
            if o.status == ObligationStatus.FULFILLED.value:
                by_party[party]["fulfilled"] += 1
            elif o.status == ObligationStatus.BREACHED.value:
                by_party[party]["breached"] += 1
            else:
                by_party[party]["pending"] += 1

        return {
            "fulfilment_pct": agreement.fulfilment_pct,
            "total": total,
            "fulfilled": fulfilled,
            "breached": breached,
            "pending": pending,
            "by_party": by_party,
        }

    # ── Breach Detection ────────────────────────────────────────────────

    def detect_breaches(self, agreement: Agreement) -> list[dict[str, Any]]:
        """Detect breaches and potential breaches."""
        breaches: list[dict[str, Any]] = []
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        for obligation in agreement.obligations:
            if obligation.status == ObligationStatus.BREACHED.value:
                breaches.append({
                    "type": "confirmed_breach",
                    "obligation_id": obligation.obligation_id,
                    "description": obligation.description,
                    "party_id": obligation.party_id,
                    "severity": "high",
                    "evidence": [{"type": "obligation_status", "value": "breached"}],
                })
                continue

            if obligation.status == ObligationStatus.PENDING.value and obligation.due_date:
                try:
                    due = datetime.fromisoformat(obligation.due_date.replace("Z", "+00:00"))
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=timezone.utc)
                    days_overdue = (now - due).days
                    if days_overdue > 0:
                        breaches.append({
                            "type": "overdue_obligation",
                            "obligation_id": obligation.obligation_id,
                            "description": f"{obligation.description} is {days_overdue} days overdue",
                            "party_id": obligation.party_id,
                            "severity": "critical" if days_overdue > 30 else "high" if days_overdue > 7 else "medium",
                            "days_overdue": days_overdue,
                            "evidence": [{"type": "overdue", "days": days_overdue}],
                        })
                except (ValueError, TypeError):
                    pass

        return breaches

    # ── Dependency Analysis ─────────────────────────────────────────────

    def analyze_dependencies(self, agreement: Agreement) -> list[dict[str, Any]]:
        """Analyze dependencies between obligations and milestones."""
        deps: list[dict[str, Any]] = []

        for dep_id in agreement.dependencies:
            blocked = [o for o in agreement.obligations if o.status not in (
                ObligationStatus.FULFILLED.value, ObligationStatus.WAIVED.value)]
            if blocked:
                deps.append({
                    "dependency": dep_id,
                    "blocked_obligations": len(blocked),
                    "blocked_details": [o.description for o in blocked[:3]],
                })

        for milestone in agreement.milestones:
            if milestone.status == "pending" and milestone.due_date:
                from datetime import datetime, timezone
                try:
                    due = datetime.fromisoformat(milestone.due_date.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) > due:
                        deps.append({
                            "dependency": f"milestone_{milestone.milestone_id}",
                            "description": f"Milestone '{milestone.title}' is overdue",
                            "blocked_obligations": 0,
                        })
                except (ValueError, TypeError):
                    pass

        return deps

    # ── Amendment Reasoning ─────────────────────────────────────────────

    def reason_about_amendments(self, agreement: Agreement) -> list[AgreementRecommendation]:
        """Recommend amendments based on agreement state."""
        recs: list[AgreementRecommendation] = []

        breached = [o for o in agreement.obligations if o.status == ObligationStatus.BREACHED.value]
        if breached:
            recs.append(AgreementRecommendation(
                title="Consider amending terms for breached obligations",
                description=f"{len(breached)} obligation(s) breached. Terms may need revision.",
                priority="high",
                reasoning=f"Obligations breached: {', '.join(o.description[:50] for o in breached[:3])}",
                confidence=0.7,
                obligations_affected=[o.obligation_id for o in breached],
                expected_outcome="Renegotiated terms that both parties can fulfil",
                evidence=[{"type": "breach_count", "value": len(breached)}],
            ))

        return recs

    # ── Renewal Recommendations ─────────────────────────────────────────

    def recommend_renewal(self, agreement: Agreement) -> AgreementRecommendation | None:
        """Recommend whether to renew an agreement."""
        if agreement.status not in (AgreementStatus.ACTIVE.value, AgreementStatus.PARTIALLY_FULFILLED.value,
                                     AgreementStatus.FULFILLED.value, AgreementStatus.EXPIRED.value):
            return None

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        is_expiring = False
        days_remaining = 365
        if agreement.end_date:
            try:
                end_str = agreement.end_date.replace("Z", "+00:00")
                end = datetime.fromisoformat(end_str)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                days_remaining = (end - now).days
                is_expiring = days_remaining < 30
            except (ValueError, TypeError):
                pass

        fulfilment = agreement.fulfilment_pct
        breached = any(o.status == ObligationStatus.BREACHED.value for o in agreement.obligations)

        if is_expiring and fulfilment >= 80 and not breached:
            return AgreementRecommendation(
                title=f"Renew '{agreement.title}' — strong fulfilment",
                description=f"Agreement expires in {days_remaining} days with {fulfilment}% fulfilment",
                priority="high",
                reasoning=f"High fulfilment ({fulfilment}%), no breaches, expiring soon",
                confidence=0.8,
                expected_outcome="Continued partnership with established terms",
                evidence=[{"type": "fulfilment_pct", "value": fulfilment},
                          {"type": "days_remaining", "value": days_remaining},
                          {"type": "no_breaches", "value": True}],
            )
        elif is_expiring and breached:
            return AgreementRecommendation(
                title=f"Re-evaluate before renewing '{agreement.title}'",
                description=f"Agreement has breaches and expires in {days_remaining} days",
                priority="high",
                reasoning="Breaches detected — terms may need renegotiation before renewal",
                confidence=0.7,
                expected_outcome="Renegotiated terms or non-renewal",
                evidence=[{"type": "fulfilment_pct", "value": fulfilment},
                          {"type": "breaches_detected", "value": True}],
            )
        elif is_expiring:
            return AgreementRecommendation(
                title=f"Review '{agreement.title}' before renewal",
                description=f"Agreement expires in {days_remaining} days. Fulfilment: {fulfilment}%",
                priority="medium",
                reasoning="Expiring soon with moderate fulfilment",
                confidence=0.6,
                expected_outcome="Informed renewal decision",
                evidence=[{"type": "fulfilment_pct", "value": fulfilment},
                          {"type": "days_remaining", "value": days_remaining}],
            )

        return None

    # ── Expiry Prediction ───────────────────────────────────────────────

    def predict_expiry(self, agreement: Agreement) -> dict[str, Any]:
        """Predict expiry risk and timeline."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if not agreement.end_date:
            return {"expiry_risk": "none", "has_end_date": False}

        try:
            end = datetime.fromisoformat(agreement.end_date.replace("Z", "+00:00"))
            days_remaining = (end - now).days
        except (ValueError, TypeError):
            return {"expiry_risk": "unknown", "error": "Invalid end_date"}

        if days_remaining <= 0:
            risk = "expired"
        elif days_remaining < 30:
            risk = "critical"
        elif days_remaining < 90:
            risk = "high"
        elif days_remaining < 180:
            risk = "medium"
        else:
            risk = "low"

        return {
            "expiry_risk": risk,
            "days_remaining": max(0, days_remaining),
            "end_date": agreement.end_date,
            "auto_renew": agreement.auto_renew,
            "recommendation": "Auto-renew will handle" if agreement.auto_renew and risk in ("critical", "high")
            else f"Review and decide on renewal — {days_remaining} days remaining",
        }

    # ── Compliance Reasoning ────────────────────────────────────────────

    def reason_about_compliance(self, agreement: Agreement) -> list[dict[str, Any]]:
        """Analyze compliance with agreement terms."""
        issues: list[dict[str, Any]] = []

        for condition in agreement.conditions:
            if not condition.is_met:
                issues.append({
                    "type": "unmet_condition",
                    "description": condition.description,
                    "severity": "high",
                    "evidence": [{"type": "condition_status", "value": "unmet"}],
                })

        for milestone in agreement.milestones:
            if milestone.status == "pending" and milestone.due_date:
                from datetime import datetime, timezone
                try:
                    due = datetime.fromisoformat(milestone.due_date.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) > due:
                        issues.append({
                            "type": "overdue_milestone",
                            "description": f"Milestone '{milestone.title}' overdue",
                            "severity": "high",
                            "evidence": [{"type": "milestone_due", "value": milestone.due_date}],
                        })
                except (ValueError, TypeError):
                    pass

        return issues

    # ── Financial Obligation Analysis ───────────────────────────────────

    def analyze_financial_obligations(self, agreement: Agreement) -> dict[str, Any]:
        """Analyze financial commitments in the agreement."""
        total = sum(fc.get("amount", 0) for fc in agreement.financial_commitments)
        fulfilled = sum(fc.get("amount", 0) for fc in agreement.financial_commitments
                        if fc.get("status") == "fulfilled")
        pending = total - fulfilled

        return {
            "total_financial_commitment": total,
            "fulfilled": fulfilled,
            "pending": pending,
            "fulfilment_pct": round((fulfilled / max(total, 1)) * 100, 1),
            "commitments": [
                {"description": fc.get("description", ""), "amount": fc.get("amount", 0),
                 "status": fc.get("status", "pending"), "due_date": fc.get("due_date", "")}
                for fc in agreement.financial_commitments
            ],
        }

    # ── Risk Scoring ────────────────────────────────────────────────────

    def score_risks(self, agreement: Agreement) -> list[dict[str, Any]]:
        """Score risks associated with the agreement."""
        risks: list[dict[str, Any]] = []

        breached = sum(1 for o in agreement.obligations if o.status == ObligationStatus.BREACHED.value)
        if breached > 0:
            risks.append({
                "type": "breach_risk",
                "score": min(1.0, breached * 0.3),
                "level": "high" if breached >= 3 else "medium",
                "description": f"{breached} breached obligation(s)",
                "mitigation": "Review and renegotiate terms for breached obligations",
            })

        pending = sum(1 for o in agreement.obligations if o.status == ObligationStatus.PENDING.value)
        if pending > 5:
            risks.append({
                "type": "accumulation_risk",
                "score": 0.5,
                "level": "medium",
                "description": f"{pending} pending obligations may accumulate",
                "mitigation": "Prioritize and track pending obligations actively",
            })

        from datetime import datetime, timezone
        if agreement.end_date:
            try:
                end = datetime.fromisoformat(agreement.end_date.replace("Z", "+00:00"))
                days = (end - datetime.now(timezone.utc)).days
                if days < 30:
                    risks.append({
                        "type": "expiry_risk",
                        "score": 0.8,
                        "level": "high",
                        "description": f"Expiring in {days} days",
                        "mitigation": "Begin renewal process immediately",
                    })
            except (ValueError, TypeError):
                pass

        return risks

    # ── Trust Impact ────────────────────────────────────────────────────

    def assess_trust_impact(self, agreement: Agreement) -> dict[str, Any]:
        """Assess impact of agreement on trust between parties."""
        breached = sum(1 for o in agreement.obligations if o.status == ObligationStatus.BREACHED.value)
        fulfilled = sum(1 for o in agreement.obligations if o.status == ObligationStatus.FULFILLED.value)
        total = len(agreement.obligations)

        if total == 0:
            return {"trust_score": 0.5, "impact": "neutral", "assessment": "no_data"}

        trust_delta = (fulfilled - breached * 2) / max(total, 1)
        trust_score = max(0.0, min(1.0, 0.5 + trust_delta * 0.3))

        if trust_score >= 0.7:
            impact = "positive"
            assessment = "strengthening"
        elif trust_score >= 0.4:
            impact = "neutral"
            assessment = "stable"
        else:
            impact = "negative"
            assessment = "eroding"

        return {"trust_score": round(trust_score, 4), "impact": impact, "assessment": assessment,
                "breached": breached, "fulfilled": fulfilled}

    # ── Execution Progress ──────────────────────────────────────────────

    def assess_execution_progress(self, agreement: Agreement) -> dict[str, Any]:
        """Assess overall execution progress of the agreement."""
        fulfilment = agreement.fulfilment_pct
        milestone_count = len(agreement.milestones)
        completed_milestones = sum(1 for m in agreement.milestones if m.status == "completed")
        condition_count = len(agreement.conditions)
        met_conditions = sum(1 for c in agreement.conditions if c.is_met)

        return {
            "fulfilment_pct": fulfilment,
            "milestones": {"total": milestone_count, "completed": completed_milestones,
                           "pct": round((completed_milestones / max(milestone_count, 1)) * 100, 1)},
            "conditions": {"total": condition_count, "met": met_conditions,
                           "pct": round((met_conditions / max(condition_count, 1)) * 100, 1)},
            "assessment": "on_track" if fulfilment >= 80 else "needs_attention" if fulfilment >= 50 else "at_risk",
        }

    # ── Explainable Recommendation ──────────────────────────────────────

    def explain_recommendation(self, rec: AgreementRecommendation) -> dict[str, Any]:
        """Package a recommendation with full explainability."""
        return {
            "recommendation": rec.title,
            "description": rec.description,
            "reasoning": rec.reasoning,
            "confidence": rec.confidence,
            "obligations_affected": rec.obligations_affected,
            "risks": rec.risks,
            "expected_outcome": rec.expected_outcome,
            "evidence": rec.evidence,
            "explanation": "This recommendation is based on the following evidence:",
            "evidence_summary": [
                {"basis": e.get("type", ""), "value": e.get("value", "")}
                for e in rec.evidence
            ],
        }

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, agreement: Agreement) -> dict[str, Any]:
        """Prepare structured context for AI understanding."""
        return {
            "agreement": {
                "title": agreement.title,
                "type": agreement.agreement_type,
                "status": agreement.status,
                "purpose": agreement.purpose,
            },
            "parties": [{"name": p.name, "role": p.role} for p in agreement.parties],
            "obligations": {
                "total": len(agreement.obligations),
                "fulfilled": sum(1 for o in agreement.obligations if o.status == ObligationStatus.FULFILLED.value),
                "breached": sum(1 for o in agreement.obligations if o.status == ObligationStatus.BREACHED.value),
                "pending": sum(1 for o in agreement.obligations if o.status == ObligationStatus.PENDING.value),
            },
            "fulfilment_pct": agreement.fulfilment_pct,
            "milestones": {"total": len(agreement.milestones),
                           "completed": sum(1 for m in agreement.milestones if m.status == "completed")},
            "financial": self.analyze_financial_obligations(agreement),
            "risks": self.score_risks(agreement),
            "trust": self.assess_trust_impact(agreement),
            "expiry": self.predict_expiry(agreement),
        }