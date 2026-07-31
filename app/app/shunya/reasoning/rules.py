"""SHUNYA — Reasoning Engine: Deterministic Rules (Phase F — Canonical).

Deterministic reasoning rules that evaluate workspace context and produce
findings and contradictions. Identical inputs always produce identical outputs.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.shunya.reasoning.models import (
    Contradiction, ContradictionSeverity, ContradictionType,
    EvidenceReference, Finding, FindingSeverity, FindingType,
)
from app.shunya.reasoning.registry import RuleDefinition, RuleResult


# ---------------------------------------------------------------------------
# Rule factory
# ---------------------------------------------------------------------------


def make_rule(name: str, fn, description: str = "", category: str = "",
              priority: int = 100, version: int = 1) -> RuleDefinition:
    return RuleDefinition(name=name, fn=fn, description=description,
                          category=category, priority=priority, version=version)


# ---------------------------------------------------------------------------
# Observation Rules — What is true
# ---------------------------------------------------------------------------


def rule_identity_present(context: Any) -> RuleResult:
    result = RuleResult(rule_name="identity_present")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    identity_section = sections.get("identity")
    if identity_section is not None:
        items = getattr(identity_section, "items", [])
        is_degraded = getattr(identity_section, "is_degraded", False)
        if items and not is_degraded:
            result.findings.append(Finding(
                finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
                fact_key="identity.present", fact_value=True,
                label="Identity information available",
                description=f"Identity section has {len(items)} item(s)",
                source="identity_engine", confidence=0.95,
                evidence=_evidence_from_section(identity_section, "identity")))
        elif is_degraded:
            result.findings.append(Finding(
                finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
                fact_key="identity.present", fact_value=False,
                label="Identity provider degraded", description="Identity section is degraded",
                source="identity_engine", confidence=0.5,
                evidence=_evidence_from_section(identity_section, "identity")))
    return result


def rule_knowledge_present(context: Any) -> RuleResult:
    result = RuleResult(rule_name="knowledge_present")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    knowledge_section = sections.get("knowledge")
    if knowledge_section is not None:
        items = getattr(knowledge_section, "items", [])
        is_degraded = getattr(knowledge_section, "is_degraded", False)
        if items and not is_degraded:
            result.findings.append(Finding(
                finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
                fact_key="knowledge.present", fact_value=True,
                label="Knowledge information available",
                description=f"Knowledge section has {len(items)} item(s)",
                source="knowledge_store", confidence=0.95,
                evidence=_evidence_from_section(knowledge_section, "knowledge")))
        elif is_degraded:
            result.findings.append(Finding(
                finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
                fact_key="knowledge.present", fact_value=False,
                label="Knowledge provider degraded", description="Knowledge section is degraded",
                source="knowledge_store", confidence=0.5,
                evidence=_evidence_from_section(knowledge_section, "knowledge")))
    return result


def rule_request_context_present(context: Any) -> RuleResult:
    result = RuleResult(rule_name="request_context_present")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    request_section = sections.get("request")
    if request_section is not None:
        items = getattr(request_section, "items", [])
        if items:
            result.findings.append(Finding(
                finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
                fact_key="request.context.present", fact_value=True,
                label="Request context available",
                description=f"Request section has {len(items)} item(s)",
                source="context_fusion_engine", confidence=0.95,
                evidence=_evidence_from_section(request_section, "request")))
    return result


def rule_context_fingerprint(context: Any) -> RuleResult:
    result = RuleResult(rule_name="context_fingerprint")
    if context is None:
        return result
    fingerprint = getattr(context, "fingerprint", "")
    if fingerprint:
        result.findings.append(Finding(
            finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
            fact_key="context.fingerprint", fact_value=fingerprint,
            label="Context fingerprint",
            description=f"Context has fingerprint: {fingerprint[:16]}...",
            source="context_fusion_engine", confidence=1.0,
            evidence=[EvidenceReference.from_context(
                getattr(context, "context_id", ""), source_name="context_fusion_engine")]))
    return result


# ---------------------------------------------------------------------------
# Gap Rules — What is missing
# ---------------------------------------------------------------------------


def rule_missing_identity(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_identity")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    identity_section = sections.get("identity")
    actor_id = getattr(context, "actor_id", "")
    if identity_section is None:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.BLOCKING.value,
            fact_key="identity.section", label="Missing identity section",
            description="No identity section found in context",
            source="context_fusion_engine"))
    elif getattr(identity_section, "is_degraded", False):
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.REQUIRED.value,
            fact_key="identity.degraded", label="Identity information degraded",
            description="Identity provider was unavailable", source="identity_engine"))
    elif not getattr(identity_section, "items", []) and actor_id:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.RECOMMENDED.value,
            fact_key="identity.no_match", label="No identity match found",
            description=f"No identity matched for actor: {actor_id}", source="identity_engine"))
    return result


def rule_missing_knowledge(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_knowledge")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    knowledge_section = sections.get("knowledge")
    if knowledge_section is None:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.REQUIRED.value,
            fact_key="knowledge.section", label="Missing knowledge section",
            description="No knowledge section found in context",
            source="context_fusion_engine"))
    elif getattr(knowledge_section, "is_degraded", False):
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.REQUIRED.value,
            fact_key="knowledge.degraded", label="Knowledge information degraded",
            description="Knowledge provider was unavailable", source="knowledge_store"))
    elif not getattr(knowledge_section, "items", []):
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.RECOMMENDED.value,
            fact_key="knowledge.empty", label="No knowledge items",
            description="Knowledge section exists but has no items",
            source="knowledge_store"))
    return result


def rule_missing_tenant(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_tenant")
    if context is None:
        return result
    tenant_id = getattr(context, "tenant_id", 0)
    if not tenant_id:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.BLOCKING.value,
            fact_key="tenant_id", label="Missing tenant ID",
            description="No tenant ID found in context", source="context_fusion_engine"))
    return result


def rule_missing_actor(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_actor")
    if context is None:
        return result
    actor_id = getattr(context, "actor_id", "")
    if not actor_id:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.BLOCKING.value,
            fact_key="actor_id", label="Missing actor ID",
            description="No actor ID found in context", source="context_fusion_engine"))
    return result


def rule_missing_purpose(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_purpose")
    if context is None:
        return result
    purpose_code = getattr(context, "purpose_code", "")
    if not purpose_code:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.REQUIRED.value,
            fact_key="purpose_code", label="Missing purpose code",
            description="No purpose code found in context", source="context_fusion_engine"))
    return result


def rule_missing_fingerprint(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_fingerprint")
    if context is None:
        return result
    fingerprint = getattr(context, "fingerprint", "")
    if not fingerprint:
        result.findings.append(Finding(
            finding_type=FindingType.GAP.value, severity=FindingSeverity.RECOMMENDED.value,
            fact_key="context.fingerprint", label="Missing context fingerprint",
            description="No fingerprint found on context", source="context_fusion_engine"))
    return result


# ---------------------------------------------------------------------------
# Contradiction Rules — What is conflicting
# ---------------------------------------------------------------------------


def rule_identity_degraded_contradiction(context: Any) -> RuleResult:
    result = RuleResult(rule_name="identity_degraded_contradiction")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    identity_section = sections.get("identity")
    is_degraded = getattr(context, "is_degraded", False)
    if identity_section and getattr(identity_section, "is_degraded", False):
        result.contradictions.append(Contradiction(
            contradiction_type=ContradictionType.FACT_CONFLICT.value,
            severity=ContradictionSeverity.HIGH.value,
            label="Identity provider degraded",
            description="Identity provider failed to respond",
            fact_keys=["identity.section"], fact_values=["degraded"],
            sources=["identity_engine"],
            resolution_guidance="Retry identity resolution or fall back to cached identity",
            rule_name="identity_degraded_contradiction",
            evidence=_evidence_from_section(identity_section, "identity")))
    if is_degraded and identity_section and getattr(identity_section, "is_degraded", False):
        pass
    elif is_degraded:
        result.contradictions.append(Contradiction(
            contradiction_type=ContradictionType.FACT_CONFLICT.value,
            severity=ContradictionSeverity.MEDIUM.value,
            label="Context degraded",
            description="Overall context assembly was degraded",
            fact_keys=["is_degraded"], fact_values=[True],
            sources=["context_fusion_engine"],
            resolution_guidance="Investigate which provider caused degradation",
            rule_name="identity_degraded_contradiction"))
    return result


def rule_knowledge_degraded_contradiction(context: Any) -> RuleResult:
    result = RuleResult(rule_name="knowledge_degraded_contradiction")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    knowledge_section = sections.get("knowledge")
    if knowledge_section and getattr(knowledge_section, "is_degraded", False):
        result.contradictions.append(Contradiction(
            contradiction_type=ContradictionType.FACT_CONFLICT.value,
            severity=ContradictionSeverity.MEDIUM.value,
            label="Knowledge provider degraded",
            description="Knowledge provider failed to respond",
            fact_keys=["knowledge.section"], fact_values=["degraded"],
            sources=["knowledge_store"],
            resolution_guidance="Retry knowledge lookup or use cached knowledge",
            rule_name="knowledge_degraded_contradiction",
            evidence=_evidence_from_section(knowledge_section, "knowledge")))
    return result


def rule_budget_truncation_contradiction(context: Any) -> RuleResult:
    result = RuleResult(rule_name="budget_truncation_contradiction")
    if context is None:
        return result
    budget = getattr(context, "budget", None)
    if budget and getattr(budget, "truncated", False):
        result.contradictions.append(Contradiction(
            contradiction_type=ContradictionType.INCOMPLETE_EVIDENCE.value,
            severity=ContradictionSeverity.MEDIUM.value,
            label="Context budget exceeded",
            description=f"Context was truncated: {getattr(budget, 'total_items', 0)} items "
                        f"(max {getattr(budget, 'max_items', 100)})",
            fact_keys=["budget.truncated", "budget.total_items", "budget.max_items"],
            fact_values=[getattr(budget, "truncated", False),
                         getattr(budget, "total_items", 0),
                         getattr(budget, "max_items", 100)],
            sources=["context_fusion_engine"],
            resolution_guidance="Increase budget limits or reduce context size",
            rule_name="budget_truncation_contradiction"))
    return result


def rule_stale_context_contradiction(context: Any) -> RuleResult:
    """Detect stale context — context older than 1 hour."""
    result = RuleResult(rule_name="stale_context_contradiction")
    if context is None:
        return result
    from datetime import datetime, timezone, timedelta
    created_at = getattr(context, "created_at", None)
    if created_at:
        age = datetime.now(timezone.utc) - created_at
        if age > timedelta(hours=1):
            result.contradictions.append(Contradiction(
                contradiction_type=ContradictionType.STALE_CONTEXT.value,
                severity=ContradictionSeverity.MEDIUM.value,
                label="Stale context detected",
                description=f"Context is {age.total_seconds() / 60:.0f} minutes old",
                fact_keys=["created_at"], fact_values=[created_at.isoformat()],
                sources=["context_fusion_engine"],
                resolution_guidance="Re-acquire fresh context before proceeding",
                rule_name="stale_context_contradiction"))
    return result


# ---------------------------------------------------------------------------
# Risk Rules — What is risky
# ---------------------------------------------------------------------------


def rule_degraded_context_risk(context: Any) -> RuleResult:
    result = RuleResult(rule_name="degraded_context_risk")
    if context is None:
        return result
    if getattr(context, "is_degraded", False):
        result.findings.append(Finding(
            finding_type=FindingType.RISK.value, severity=FindingSeverity.HIGH.value,
            fact_key="is_degraded", label="Degraded context risk",
            description="Context assembly was degraded — information may be incomplete",
            source="reasoning_engine"))
    return result


def rule_missing_identity_risk(context: Any) -> RuleResult:
    result = RuleResult(rule_name="missing_identity_risk")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    identity_section = sections.get("identity")
    if identity_section is None or getattr(identity_section, "is_degraded", False):
        result.findings.append(Finding(
            finding_type=FindingType.RISK.value, severity=FindingSeverity.HIGH.value,
            fact_key="identity.section", label="Missing identity risk",
            description="Cannot identify the requesting actor",
            source="identity_engine"))
    return result


def rule_budget_truncation_risk(context: Any) -> RuleResult:
    result = RuleResult(rule_name="budget_truncation_risk")
    if context is None:
        return result
    budget = getattr(context, "budget", None)
    if budget and getattr(budget, "truncated", False):
        result.findings.append(Finding(
            finding_type=FindingType.RISK.value, severity=FindingSeverity.MEDIUM.value,
            fact_key="budget.truncated", label="Context truncation risk",
            description=f"Context limited to {getattr(budget, 'max_items', 100)} items — "
                        f"some information may be missing",
            source="context_fusion_engine"))
    return result


def rule_no_evidence_risk(context: Any) -> RuleResult:
    result = RuleResult(rule_name="no_evidence_risk")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    total_items = sum(len(getattr(s, "items", [])) for s in sections.values())
    if total_items == 0:
        result.findings.append(Finding(
            finding_type=FindingType.RISK.value, severity=FindingSeverity.CRITICAL.value,
            fact_key="sections", label="No evidence available",
            description="No context items were found from any provider",
            source="context_fusion_engine"))
    return result


# ---------------------------------------------------------------------------
# Attention rules
# ---------------------------------------------------------------------------


def rule_attention_items(context: Any) -> RuleResult:
    result = RuleResult(rule_name="attention_items")
    if context is None:
        return result
    sections = getattr(context, "sections", {}) or {}
    is_degraded = getattr(context, "is_degraded", False)
    if is_degraded:
        result.findings.append(Finding(
            finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
            fact_key="attention.requires_attention", fact_value=True,
            label="Context requires attention",
            description="Context is degraded — review before use",
            source="reasoning_engine", confidence=1.0))
    for name, section in sections.items():
        if getattr(section, "is_degraded", False):
            result.findings.append(Finding(
                finding_type=FindingType.OBSERVATION.value, severity=FindingSeverity.INFO.value,
                fact_key=f"attention.{name}_degraded", fact_value=True,
                label=f"{name} provider degraded",
                description=f"The {name} provider returned degraded data",
                source="reasoning_engine", confidence=1.0,
                evidence=_evidence_from_section(section, name)))
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _evidence_from_section(section: Any, section_name: str) -> List[EvidenceReference]:
    references: List[EvidenceReference] = []
    if section is None:
        return references
    source_name = {"identity": "identity_engine", "knowledge": "knowledge_store",
                   "request": "context_fusion_engine"}.get(section_name, "context_fusion_engine")
    items = getattr(section, "items", [])
    for item in items[:5]:
        if isinstance(item, dict):
            references.append(EvidenceReference(source_name=source_name,
                                                 confidence=0.9, metadata={"item": item}))
    return references


# ---------------------------------------------------------------------------
# Standard rule sets
# ---------------------------------------------------------------------------

OBSERVATION_RULES = [
    make_rule("identity_present", rule_identity_present, category="observation", priority=10),
    make_rule("knowledge_present", rule_knowledge_present, category="observation", priority=20),
    make_rule("request_context_present", rule_request_context_present, category="observation", priority=30),
    make_rule("context_fingerprint", rule_context_fingerprint, category="observation", priority=40),
]

GAP_RULES = [
    make_rule("missing_identity", rule_missing_identity, category="gap", priority=100),
    make_rule("missing_knowledge", rule_missing_knowledge, category="gap", priority=110),
    make_rule("missing_tenant", rule_missing_tenant, category="gap", priority=120),
    make_rule("missing_actor", rule_missing_actor, category="gap", priority=130),
    make_rule("missing_purpose", rule_missing_purpose, category="gap", priority=140),
    make_rule("missing_fingerprint", rule_missing_fingerprint, category="gap", priority=150),
]

CONTRADICTION_RULES = [
    make_rule("identity_degraded_contradiction", rule_identity_degraded_contradiction,
              category="contradiction", priority=200),
    make_rule("knowledge_degraded_contradiction", rule_knowledge_degraded_contradiction,
              category="contradiction", priority=210),
    make_rule("budget_truncation_contradiction", rule_budget_truncation_contradiction,
              category="contradiction", priority=220),
    make_rule("stale_context_contradiction", rule_stale_context_contradiction,
              category="contradiction", priority=230),
]

RISK_RULES = [
    make_rule("degraded_context_risk", rule_degraded_context_risk, category="risk", priority=300),
    make_rule("missing_identity_risk", rule_missing_identity_risk, category="risk", priority=310),
    make_rule("budget_truncation_risk", rule_budget_truncation_risk, category="risk", priority=320),
    make_rule("no_evidence_risk", rule_no_evidence_risk, category="risk", priority=330),
]

ATTENTION_RULES = [
    make_rule("attention_items", rule_attention_items, category="composite", priority=500),
]

ALL_STANDARD_RULES = (
    OBSERVATION_RULES + GAP_RULES + CONTRADICTION_RULES +
    RISK_RULES + ATTENTION_RULES
)


def register_standard_rules(registry: Any) -> None:
    from app.shunya.reasoning.registry import RuleRegistry
    for rule_def in ALL_STANDARD_RULES:
        registry.register(rule_def)