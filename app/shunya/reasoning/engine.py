"""SHUNYA — Reasoning Engine (Phase F — Canonical).

Facade that orchestrates rule execution, evidence graph building,
confidence assessment, and infrastructure integration.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.shunya.reasoning.confidence import ConfidenceEngine
from app.shunya.reasoning.evidence_graph import EvidenceGraph
from app.shunya.reasoning.models import (
    ConfidenceScore, Contradiction, ContradictionSeverity,
    Finding, FindingSeverity, FindingType,
    ReasoningMetadata, ReasoningResult,
)
from app.shunya.reasoning.registry import RuleRegistry, RuleResult
from app.shunya.reasoning.rules import register_standard_rules


class ReasoningEngine:
    """Reasoning Engine — evaluates a WorkspaceContext and produces an
    immutable ReasoningResult.

    The engine identifies:
      - What is true        (findings with finding_type="observation")
      - What is missing     (findings with finding_type="gap")
      - What is conflicting (contradictions)
      - What is risky       (findings with finding_type="risk")
      - What requires attention (attention_items)

    The engine does NOT:
      - Generate plans, execute actions, invoke LLMs, produce prompts,
        or make autonomous decisions.

    Deterministic: identical inputs always produce identical outputs.
    """

    def __init__(self, rule_registry: Optional[RuleRegistry] = None,
                 confidence_engine: Optional[ConfidenceEngine] = None,
                 identity_engine: Any = None,
                 knowledge_store: Any = None, logger: Any = None,
                 metrics_registry: Any = None, health_registry: Any = None,
                 event_bus: Any = None) -> None:
        self._registry = rule_registry or RuleRegistry()
        self._confidence = confidence_engine or ConfidenceEngine()
        self._identity_engine = identity_engine
        self._knowledge_store = knowledge_store
        self._logger = logger
        self._metrics = metrics_registry
        self._health = health_registry
        self._event_bus = event_bus

        register_standard_rules(self._registry)

        if self._metrics:
            self._reasoning_counter = self._metrics.counter(
                "reasoning_evaluations_total", "Reasoning evaluations")
            self._healthy_counter = self._metrics.counter(
                "reasoning_healthy_total", "Healthy reasoning results")
            self._contradiction_counter = self._metrics.counter(
                "reasoning_contradictions_total", "Contradictions detected")
            self._gap_counter = self._metrics.counter(
                "reasoning_gaps_total", "Gaps detected")
            self._risk_counter = self._metrics.counter(
                "reasoning_risks_total", "Risks detected")
            self._latency_histogram = self._metrics.histogram(
                "reasoning_evaluation_latency_ms", "Evaluation latency",
                buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000])

        if self._health:
            self._health.register("reasoning_engine", self._health_check)

    def evaluate(self, context: Any) -> ReasoningResult:
        start = time.time()
        context_id = getattr(context, "context_id", "")

        if self._logger:
            self._logger.info("Evaluating context", extra={
                "context_id": context_id, "rules": self._registry.enabled_count})

        rule_results = self._registry.execute_all(context)
        elapsed_ms = (time.time() - start) * 1000

        findings: List[Finding] = []
        contradictions: List[Contradiction] = []
        attention_items: List[str] = []
        rules_passed = 0
        rules_failed = 0

        for rr in rule_results:
            findings.extend(rr.findings)
            contradictions.extend(rr.contradictions)
            if rr.passed:
                rules_passed += 1
            else:
                rules_failed += 1
                if rr.error:
                    attention_items.append(f"Rule '{rr.rule_name}' failed: {rr.error}")

        for f in findings:
            if f.finding_type == FindingType.GAP.value and f.severity in ("blocking", "required"):
                attention_items.append(f"Missing: {f.label}")
            if f.finding_type == FindingType.RISK.value and f.severity in ("critical", "high"):
                attention_items.append(f"Risk: {f.label}")
        for c in contradictions:
            if c.severity in ("critical", "high"):
                attention_items.append(f"Contradiction: {c.label}")

        confidence = self._confidence.assess(findings, contradictions)

        metadata = ReasoningMetadata(
            context_id=context_id,
            correlation_id=getattr(context, "provenance", None) and
                          getattr(context.provenance, "correlation_id", "") or "",
            elapsed_ms=elapsed_ms,
            rules_executed=len(rule_results),
            rules_passed=rules_passed,
            rules_failed=rules_failed,
        )

        result = ReasoningResult(
            findings=findings, contradictions=contradictions,
            attention_items=attention_items, confidence=confidence,
            metadata=metadata,
        )

        self._record_metrics(start, result)
        if self._event_bus:
            self._emit_event(result)
        return result

    def execute_rule(self, rule_name: str, context: Any) -> Optional[RuleResult]:
        return self._registry.execute_by_name(rule_name, context)

    def build_evidence_graph(self, result: ReasoningResult) -> EvidenceGraph:
        graph = EvidenceGraph()
        graph.add_reasoning_result(result)
        return graph

    @property
    def registry(self) -> RuleRegistry:
        return self._registry

    def _health_check(self) -> Any:
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus
        status = HealthStatus.HEALTHY
        detail = "Reasoning Engine operational"
        metrics_dict = {"rules_registered": self._registry.count,
                        "rules_enabled": self._registry.enabled_count}
        if self._registry.count == 0:
            status = HealthStatus.DEGRADED
            detail = "No rules registered"
        return HealthCheckResult(component="reasoning_engine", status=status,
                                 detail=detail, metrics=metrics_dict)

    def _emit_event(self, result: ReasoningResult) -> None:
        from app.shunya.infrastructure.event_bus import CanonicalEvent
        event = CanonicalEvent(
            event_type="reasoning.evaluation.completed",
            actor_name="reasoning_engine", object_id=result.result_id,
            object_type="reasoning_result",
            payload={
                "result_id": result.result_id,
                "has_contradictions": result.has_contradictions,
                "has_gaps": result.has_gaps, "has_risks": result.has_risks,
                "is_healthy": result.is_healthy,
                "requires_attention": result.requires_attention,
                "findings": len(result.findings),
                "contradictions": len(result.contradictions),
                "confidence_score": result.confidence.overall_score if result.confidence else 0.0,
                "confidence_level": result.confidence.level if result.confidence else "unknown",
            },
        )
        self._event_bus.publish(event)

    def _record_metrics(self, start: float, result: ReasoningResult) -> None:
        duration = (time.time() - start) * 1000
        if self._metrics:
            self._reasoning_counter.inc()
            self._latency_histogram.observe(duration)
            if result.confidence and result.is_healthy:
                self._healthy_counter.inc()
            if result.contradictions:
                self._contradiction_counter.inc(len(result.contradictions))
            if result.gaps:
                self._gap_counter.inc(len(result.gaps))
            if result.risks:
                self._risk_counter.inc(len(result.risks))


# ---- Module-level convenience -----------------------------------------------

_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine(**kwargs: Any) -> ReasoningEngine:
    global _engine
    if _engine is None:
        _engine = ReasoningEngine(**kwargs)
    return _engine


def reset_reasoning_engine() -> None:
    global _engine
    _engine = None