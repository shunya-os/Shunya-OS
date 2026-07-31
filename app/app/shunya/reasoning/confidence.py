"""SHUNYA — Reasoning Engine: Confidence Engine (Phase F — Canonical).

Deterministic confidence scoring using only:
  - Completeness: What fraction of required facts are present
  - Consistency: How consistent the facts are (no contradictions)
  - Freshness: How recent the facts are
  - Corroboration: How many independent sources confirm each fact
  - Provenance quality: How reliable the sources are

No AI-derived confidence. No statistical inference.
All scores are deterministic given the same inputs.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

from app.shunya.reasoning.models import (
    ConfidenceScore, ConfidenceLevel, Contradiction,
    ContradictionSeverity, EvidenceReference, Finding,
    FindingSeverity, FindingType,
)


FRESHNESS_WINDOWS = [
    (timedelta(minutes=5), 1.0),
    (timedelta(hours=1), 0.95),
    (timedelta(hours=6), 0.85),
    (timedelta(days=1), 0.75),
    (timedelta(days=7), 0.60),
    (timedelta(days=30), 0.40),
    (timedelta(days=90), 0.20),
    (timedelta(days=365), 0.10),
]

PROVENANCE_WEIGHTS = {
    "knowledge_store": 1.0,
    "identity_engine": 1.0,
    "context_fusion_engine": 0.95,
    "reasoning_engine": 0.90,
    "external": 0.6,
}

REQUIRED_FACT_KEYS: Set[str] = {
    "identity.present",
    "knowledge.present",
    "request.context.present",
    "context.fingerprint",
}


class ConfidenceEngine:
    """Deterministic confidence scoring engine."""

    def __init__(self) -> None:
        self._weights = {
            "completeness": 0.30,
            "consistency": 0.25,
            "freshness": 0.15,
            "corroboration": 0.15,
            "provenance_quality": 0.15,
        }

    def assess(self, findings: List[Finding],
               contradictions: List[Contradiction]) -> ConfidenceScore:
        completeness = self._compute_completeness(findings)
        consistency = self._compute_consistency(contradictions)
        freshness = self._compute_freshness(findings)
        corroboration = self._compute_corroboration(findings)
        provenance_quality = self._compute_provenance_quality(findings)

        overall = (
            self._weights["completeness"] * completeness
            + self._weights["consistency"] * consistency
            + self._weights["freshness"] * freshness
            + self._weights["corroboration"] * corroboration
            + self._weights["provenance_quality"] * provenance_quality
        )

        observations = [f for f in findings if f.finding_type == FindingType.OBSERVATION.value]
        present_keys = set(o.fact_key for o in observations)
        required_present = len(present_keys & REQUIRED_FACT_KEYS)
        required_total = len(REQUIRED_FACT_KEYS)

        return ConfidenceScore(
            overall_score=round(overall, 4),
            level=ConfidenceScore.compute_level(overall),
            completeness_score=round(completeness, 4),
            consistency_score=round(consistency, 4),
            freshness_score=round(freshness, 4),
            corroboration_score=round(corroboration, 4),
            provenance_quality_score=round(provenance_quality, 4),
            total_findings=len(findings),
            total_contradictions=len(contradictions),
            total_assumptions=0,
            total_constraints=0,
            required_facts_present=required_present,
            required_facts_total=required_total,
        )

    def _compute_completeness(self, findings: List[Finding]) -> float:
        observations = [f for f in findings if f.finding_type == FindingType.OBSERVATION.value]
        present_keys = set(o.fact_key for o in observations)
        if not REQUIRED_FACT_KEYS:
            return 1.0
        required_present = len(present_keys & REQUIRED_FACT_KEYS)
        required_score = required_present / len(REQUIRED_FACT_KEYS)
        gaps = [f for f in findings if f.finding_type == FindingType.GAP.value]
        blocking_gaps = sum(1 for g in gaps if g.severity == FindingSeverity.BLOCKING.value)
        required_gaps = sum(1 for g in gaps if g.severity == FindingSeverity.REQUIRED.value)
        gap_penalty = 1.0 - (blocking_gaps * 0.25 + required_gaps * 0.10)
        gap_penalty = max(0.0, gap_penalty)
        return round(required_score * gap_penalty, 4)

    def _compute_consistency(self, contradictions: List[Contradiction]) -> float:
        if not contradictions:
            return 1.0
        total_penalty = 0.0
        for c in contradictions:
            if c.severity == ContradictionSeverity.CRITICAL.value:
                total_penalty += 0.40
            elif c.severity == ContradictionSeverity.HIGH.value:
                total_penalty += 0.25
            elif c.severity == ContradictionSeverity.MEDIUM.value:
                total_penalty += 0.15
            elif c.severity == ContradictionSeverity.LOW.value:
                total_penalty += 0.05
            elif c.severity == ContradictionSeverity.INFO.value:
                total_penalty += 0.02
        score = max(0.05, 1.0 - min(total_penalty, 0.95))
        return round(score, 4)

    def _compute_freshness(self, findings: List[Finding]) -> float:
        if not findings:
            return 0.0
        now = datetime.now(timezone.utc)
        scores: List[float] = []
        for f in findings:
            created = f.created_at
            if created is None:
                scores.append(0.5)
                continue
            age = now - created
            score = 0.0
            for window, fs in FRESHNESS_WINDOWS:
                if age <= window:
                    score = fs
                    break
            if score == 0.0:
                score = 0.05
            scores.append(score)
        return round(sum(scores) / len(scores), 4)

    def _compute_corroboration(self, findings: List[Finding]) -> float:
        if not findings:
            return 0.0
        fact_sources: Dict[str, Set[str]] = {}
        for f in findings:
            key = f.fact_key
            if key not in fact_sources:
                fact_sources[key] = set()
            if f.source:
                fact_sources[key].add(f.source)
            for ref in f.evidence:
                if ref.source_name:
                    fact_sources[key].add(ref.source_name)
        if not fact_sources:
            return 0.0
        scores: List[float] = []
        for key, sources in fact_sources.items():
            n = len(sources)
            scores.append(0.0 if n == 0 else 0.5 if n == 1 else 0.8 if n == 2 else 1.0)
        return round(sum(scores) / len(scores), 4)

    def _compute_provenance_quality(self, findings: List[Finding]) -> float:
        if not findings:
            return 0.0
        all_sources: Set[str] = set()
        for f in findings:
            if f.source:
                all_sources.add(f.source)
            for ref in f.evidence:
                if ref.source_name:
                    all_sources.add(ref.source_name)
        if not all_sources:
            return 0.0
        total_weight = sum(PROVENANCE_WEIGHTS.get(s, 0.5) for s in all_sources)
        return round(total_weight / len(all_sources), 4)

    @property
    def weights(self) -> Dict[str, float]:
        return dict(self._weights)