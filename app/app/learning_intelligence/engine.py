"""SHUNYA — Learning Intelligence Engine (Milestone II).

Ten sub-engines coordinated by the RuntimeService, all operating
deterministically on learning data. Reads from existing ClosedLearningLoop
and ES-007 LearningEngine — never duplicates state.

No paid-model dependency. Every learned conclusion traced to evidence.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from app.learning_intelligence.models import (
    LearningCategory, PatternStrength, ConfidenceFactor, SimilarityMetric,
    LearnedPattern, OutcomeProfile, RefinedRecommendation,
    ConfidenceAssessment, FactorContribution,
    SimilarExecution, SimilarityResult,
    OrgLearningProfile, OrgLearningInsight,
    KnowledgeEpoch, EvolutionEntry,
    LearningArtifact, LearningMemoryEntry,
    LearnerConfig, LearnerFilter, LearnerStats,
)

# =========================================================================
# Singleton
# =========================================================================

_ENGINE: Optional[LearningIntelligenceEngine] = None


def get_learning_intelligence() -> LearningIntelligenceEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = LearningIntelligenceEngine()
    return _ENGINE


def reset_learning_intelligence() -> None:
    global _ENGINE
    _ENGINE = None


# =========================================================================
# 1. Pattern Recognition Engine
# =========================================================================

class PatternRecognitionEngine:
    """Identify recurring patterns from execution outcomes.

    Analyzes outcome observations grouped by signature dimensions
    (commitment_type × result) to find statistically significant patterns.
    """

    def __init__(self, config: Optional[LearnerConfig] = None):
        self._config = config or LearnerConfig()
        self._patterns: Dict[str, LearnedPattern] = {}

    def learn(self, observations: List[Dict[str, Any]],
              tenant_id: int) -> List[LearnedPattern]:
        """Discover patterns from a batch of outcome observations."""
        # Group by signature (dimension x outcome)
        groups: Dict[str, List[Dict]] = defaultdict(list)
        for obs in observations:
            sig = self._compute_signature(obs)
            groups[sig].append(obs)

        new_patterns = []
        for sig, group in groups.items():
            existing = self._find_by_signature(sig, tenant_id)

            # Always update existing patterns; only discover new ones above threshold
            if existing:
                existing.observation_ids = list(set(
                    existing.observation_ids + [o.get("observation_id", "") for o in group]
                ))[:20]
                existing.frequency = existing.frequency + len(group)
                existing.confidence = self._compute_pattern_confidence(existing.frequency, 0.5)
                existing.strength = self._classify_strength(existing.frequency, 0.5).value
                existing.last_observed = datetime.now(timezone.utc).isoformat()
                new_patterns.append(existing)
                continue

            if len(group) < self._config.min_pattern_frequency:
                continue
            outcomes = [o.get("value") for o in group]
            success_count = sum(1 for v in outcomes if v is True
                                or (isinstance(v, str) and v.lower() in ("success", "completed", "pass")))
            total = len(outcomes)
            rate = success_count / total if total > 0 else 0.0

            name = self._derive_name(sig, group[0])
            strength = self._classify_strength(total, rate)
            confidence = self._compute_pattern_confidence(total, rate)

            pattern = LearnedPattern(
                tenant_id=tenant_id,
                name=name,
                description=f"{name}: {success_count}/{total} successful ({rate:.0%})",
                strength=strength.value,
                frequency=total,
                confidence=confidence,
                signature=sig,
                observation_ids=[o.get("observation_id", "") for o in group[:20]],
                evidence=[f"sample_count={total}", f"success_rate={rate:.2f}",
                          f"pattern_strength={strength.value}"],
            )
            self._patterns[pattern.pattern_id] = pattern
            new_patterns.append(pattern)

        return new_patterns

    def get_patterns(self, tenant_id: int) -> List[LearnedPattern]:
        return [p for p in self._patterns.values() if p.tenant_id == tenant_id]

    def get_pattern(self, pattern_id: str) -> Optional[LearnedPattern]:
        return self._patterns.get(pattern_id)

    def _compute_signature(self, obs: Dict) -> str:
        dim = obs.get("dimension", obs.get("target_id", "unknown"))
        val = obs.get("dimension_value", obs.get("outcome_type", "unknown"))
        raw = f"{dim}:{val}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _derive_name(self, sig: str, obs: Dict) -> str:
        dim = obs.get("dimension", obs.get("target_id", "pattern"))
        return f"{dim}_pattern"

    def _classify_strength(self, count: int, rate: float) -> PatternStrength:
        if count < 3:
            return PatternStrength.INCONCLUSIVE
        elif count >= 20 and (rate >= 0.8 or rate <= 0.2):
            return PatternStrength.STRONG
        elif count >= 10:
            return PatternStrength.MODERATE
        return PatternStrength.WEAK

    def _compute_pattern_confidence(self, count: int, rate: float) -> float:
        if count < 3:
            return 0.0
        sample_factor = min(1.0, count / 30)
        consistency = 1.0 - abs(rate - 0.5) * 2  # 0 at random, 1 at deterministic
        return round(sample_factor * consistency, 4)

    def _find_by_signature(self, sig: str, tenant_id: int) -> Optional[LearnedPattern]:
        for p in self._patterns.values():
            if p.signature == sig and p.tenant_id == tenant_id:
                return p
        return None


# =========================================================================
# 2. Outcome Learning Engine
# =========================================================================

class OutcomeLearningEngine:
    """Learn success/failure rates per dimension from execution outcomes.

    Builds OutcomeProfile objects for each dimension × value combination.
    Merges new observations into existing profiles incrementally.
    """

    def __init__(self):
        self._profiles: Dict[str, OutcomeProfile] = {}

    def learn(self, outcomes: List[Dict[str, Any]],
              tenant_id: int) -> List[OutcomeProfile]:
        """Update outcome profiles from a batch of outcomes."""
        groups: Dict[str, List[Dict]] = defaultdict(list)
        for o in outcomes:
            dim = o.get("dimension", o.get("commitment_type", "unknown"))
            val = o.get("dimension_value", o.get("state", "unknown"))
            key = f"{tenant_id}:{dim}:{val}"
            groups[key].append(o)

        updated = []
        for key, group in groups.items():
            parts = key.split(":", 2)
            dim, val = parts[1], parts[2]
            existing = self._profiles.get(key)

            successful = sum(1 for o in group if o.get("success", False)
                             or o.get("state") in ("fulfilled", "completed", "satisfied"))
            total = len(group)
            durations = [o.get("duration_seconds", 0) for o in group
                         if o.get("duration_seconds") is not None]
            avg_dur = sum(durations) / len(durations) if durations else None

            if existing:
                new_total = existing.total_outcomes + total
                new_success = existing.successful + successful
                rate = new_success / new_total if new_total > 0 else 0.0
                existing.successful = new_success
                existing.total_outcomes = new_total
                existing.success_rate = round(rate, 4)
                existing.updated_at = datetime.now(timezone.utc).isoformat()
                if avg_dur is not None:
                    existing.avg_duration_seconds = (
                        (existing.avg_duration_seconds or 0) * (new_total - total)
                        + sum(durations)
                    ) / new_total if new_total > 0 else avg_dur
                updated.append(existing)
            else:
                rate = successful / total if total > 0 else 0.0
                profile = OutcomeProfile(
                    tenant_id=tenant_id,
                    dimension=dim,
                    dimension_value=val,
                    total_outcomes=total,
                    successful=successful,
                    failed=total - successful,
                    success_rate=round(rate, 4),
                    avg_duration_seconds=avg_dur,
                    evidence=[f"sample_count={total}", f"success_rate={rate:.2f}"],
                )
                self._profiles[key] = profile
                updated.append(profile)

        return updated

    def get_profile(self, dimension: str, dimension_value: str,
                    tenant_id: int) -> Optional[OutcomeProfile]:
        return self._profiles.get(f"{tenant_id}:{dimension}:{dimension_value}")

    def get_profiles(self, tenant_id: int) -> List[OutcomeProfile]:
        return [p for p in self._profiles.values() if p.tenant_id == tenant_id]


# =========================================================================
# 3. Recommendation Learning Engine
# =========================================================================

class RecommendationLearning:
    """Refine next-action recommendations based on historical outcomes.

    Tracks how often each action type succeeded in various contexts
    and adjusts priority recommendations accordingly.
    """

    def __init__(self):
        self._recommendations: Dict[str, RefinedRecommendation] = {}

    def learn(self, outcomes: List[Dict[str, Any]],
              tenant_id: int) -> List[RefinedRecommendation]:
        """Update recommendation refinements from outcomes."""
        groups: Dict[str, List[Dict]] = defaultdict(list)
        for o in outcomes:
            action = o.get("action_type", o.get("recommendation_type", "unknown"))
            context = o.get("context_signature", o.get("condition_signature", "default"))
            key = f"{tenant_id}:{action}:{context}"
            groups[key].append(o)

        updated = []
        for key, group in groups.items():
            parts = key.split(":", 2)
            action, ctx = parts[1], parts[2]
            existing = self._recommendations.get(key)

            successful = sum(1 for o in group if o.get("success", False))
            total = len(group)

            if existing:
                new_total = existing.historical_count + total
                new_success = int(existing.historical_success_rate * existing.historical_count) + successful
                rate = new_success / new_total if new_total > 0 else 0.0
                existing.historical_count = new_total
                existing.historical_success_rate = round(rate, 4)
                existing.confidence = self._compute_rec_confidence(new_total, rate)
                existing.priority_adjustment = self._compute_adjustment(rate)
                existing.updated_at = datetime.now(timezone.utc).isoformat()
                updated.append(existing)
            else:
                rate = successful / total if total > 0 else 0.0
                rec = RefinedRecommendation(
                    tenant_id=tenant_id, action_type=action,
                    context_signature=ctx,
                    historical_success_rate=round(rate, 4),
                    historical_count=total,
                    confidence=self._compute_rec_confidence(total, rate),
                    priority_adjustment=self._compute_adjustment(rate),
                    evidence=[f"sample_count={total}", f"success_rate={rate:.2f}"],
                )
                self._recommendations[key] = rec
                updated.append(rec)

        return updated

    def get_recommendation(self, action_type: str, context: str,
                           tenant_id: int) -> Optional[RefinedRecommendation]:
        return self._recommendations.get(f"{tenant_id}:{action_type}:{context}")

    def get_all(self, tenant_id: int) -> List[RefinedRecommendation]:
        return [r for r in self._recommendations.values() if r.tenant_id == tenant_id]

    def _compute_rec_confidence(self, count: int, rate: float) -> float:
        sample = min(1.0, count / 20)
        consistency = abs(rate - 0.5) * 2
        return round(sample * consistency, 4)

    def _compute_adjustment(self, rate: float) -> int:
        if rate >= 0.9:
            return -1  # boost priority (lower number = higher urgency)
        elif rate <= 0.3:
            return 1   # demote priority
        return 0


# =========================================================================
# 4. Confidence Model
# =========================================================================

class ConfidenceModel:
    """Explicit factor-based confidence computation.

    Every confidence score is decomposed into named factors with
    individual weights, values, and contributions.
    """

    def assess(self, target_type: str, target_id: str,
               tenant_id: int, sample_count: int,
               success_rate: float, consistency: float = 0.5,
               recency_hours: Optional[float] = None,
               evidence_quality: float = 0.5) -> ConfidenceAssessment:
        """Compute confidence from explicit factors."""
        factors: List[FactorContribution] = []

        # Factor 1: Sample size
        sample_val = min(1.0, sample_count / 30)
        factors.append(FactorContribution(
            factor=ConfidenceFactor.SAMPLE_SIZE.value,
            value=sample_val, weight=0.30,
            contribution=sample_val * 0.30,
            explanation=f"{sample_count} samples (max 30)",
        ))

        # Factor 2: Consistency (how far from random)
        consistency_val = consistency
        factors.append(FactorContribution(
            factor=ConfidenceFactor.CONSISTENCY.value,
            value=consistency_val, weight=0.25,
            contribution=consistency_val * 0.25,
            explanation=f"consistency={consistency_val:.2f}",
        ))

        # Factor 3: Recency (if available)
        recency_val = 0.5
        if recency_hours is not None:
            recency_val = max(0.1, 1.0 - recency_hours / 720.0)  # decay over 30 days
        factors.append(FactorContribution(
            factor=ConfidenceFactor.RECENCY.value,
            value=recency_val, weight=0.20,
            contribution=recency_val * 0.20,
            explanation=f"recency={recency_val:.2f}",
        ))

        # Factor 4: Evidence quality
        eq_val = min(1.0, evidence_quality)
        factors.append(FactorContribution(
            factor=ConfidenceFactor.EVIDENCE_QUALITY.value,
            value=eq_val, weight=0.15,
            contribution=eq_val * 0.15,
            explanation=f"evidence_quality={eq_val:.2f}",
        ))

        # Factor 5: Deviation magnitude (from expected rate of 0.5)
        dev_val = abs(success_rate - 0.5) * 2
        factors.append(FactorContribution(
            factor=ConfidenceFactor.DEVIATION_MAGNITUDE.value,
            value=min(1.0, dev_val), weight=0.10,
            contribution=min(1.0, dev_val) * 0.10,
            explanation=f"deviation={dev_val:.2f}",
        ))

        overall = sum(f.contribution for f in factors)

        return ConfidenceAssessment(
            tenant_id=tenant_id, target_type=target_type,
            target_id=target_id, overall=round(overall, 4),
            factors=factors,
        )


# =========================================================================
# 5. Similarity Engine
# =========================================================================

class SimilarityEngine:
    """Find similar executions based on structural characteristics.

    Compares executions across dimensions: state, obligation types,
    outcomes, duration proximity, and resource patterns.
    """

    def find_similar(self, exec_data: Dict[str, Any],
                     candidates: List[Dict[str, Any]],
                     tenant_id: int) -> SimilarityResult:
        """Find similar executions to the query execution."""
        matches: List[SimilarExecution] = []
        exec_id = exec_data.get("exec_id", "")
        query_obl_types = set(exec_data.get("obligation_types", []))
        query_state = exec_data.get("state", "")
        query_outcome = exec_data.get("outcome", "")
        query_duration = exec_data.get("duration_seconds")

        for cand in candidates:
            if cand.get("exec_id") == exec_id:
                continue
            score, dims = self._compute_similarity(
                query_obl_types, query_state, query_outcome, query_duration,
                set(cand.get("obligation_types", [])),
                cand.get("state", ""), cand.get("outcome", ""),
                cand.get("duration_seconds"),
            )
            if score >= LearnerConfig().similarity_match_threshold:
                matches.append(SimilarExecution(
                    source_exec_id=exec_id,
                    target_exec_id=cand.get("exec_id", ""),
                    similarity_score=score,
                    matching_dimensions=dims,
                    evidence=[f"score={score:.2f}", f"dimensions={','.join(dims)}"],
                ))

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        max_matches = LearnerConfig().max_similarity_matches
        return SimilarityResult(
            query_exec_id=exec_id, tenant_id=tenant_id,
            matches=matches[:max_matches],
            total_candidates=len(candidates),
        )

    def _compute_similarity(self, q_obls: Set[str], q_state: str,
                            q_outcome: str, q_dur: Optional[float],
                            c_obls: Set[str], c_state: str,
                            c_outcome: str, c_dur: Optional[float]) -> Tuple[float, List[str]]:
        dims = []
        score = 0.0

        # State match: exact match = 0.4
        if q_state and q_state == c_state:
            score += 0.4
            dims.append("state")

        # Obligation type overlap
        if q_obls and c_obls:
            overlap = len(q_obls & c_obls)
            union = len(q_obls | c_obls)
            obl_score = overlap / union if union > 0 else 0.0
            score += obl_score * 0.3
            if obl_score > 0:
                dims.append("obligation_types")

        # Outcome match
        if q_outcome and q_outcome == c_outcome:
            score += 0.2
            dims.append("outcome")

        # Duration proximity
        if q_dur is not None and c_dur is not None and q_dur > 0 and c_dur > 0:
            ratio = min(q_dur, c_dur) / max(q_dur, c_dur)
            score += ratio * 0.1
            if ratio > 0.8:
                dims.append("duration")

        return round(score, 4), dims


# =========================================================================
# 6. Organizational Learning
# =========================================================================

class OrganizationalLearning:
    """Cross-role and cross-unit learning patterns.

    Aggregates learning by organizational unit and role to identify
    unit-specific patterns and cross-unit insights.
    """

    def __init__(self):
        self._insights: Dict[str, OrgLearningInsight] = {}

    def learn(self, outcomes: List[Dict[str, Any]],
              tenant_id: int, unit_id: str = "",
              role_id: str = "") -> List[OrgLearningInsight]:
        """Generate organizational learning insights from outcomes."""
        insights: List[OrgLearningInsight] = []
        groups: Dict[str, List[Dict]] = defaultdict(list)
        for o in outcomes:
            dim = o.get("dimension", "general")
            key = f"{tenant_id}:{unit_id}:{role_id}:{dim}"
            groups[key].append(o)

        for key, group in groups.items():
            parts = key.split(":")
            _, u_id, r_id, dim = parts[0], parts[1], parts[2], parts[3]
            successful = sum(1 for o in group if o.get("success", False))
            total = len(group)
            rate = successful / total if total > 0 else 0.0

            existing_key = f"{key}:{datetime.now(timezone.utc).date().isoformat()}"
            insight = OrgLearningInsight(
                tenant_id=tenant_id, unit_id=u_id, role_id=r_id,
                dimension=dim,
                observation=f"{successful}/{total} successful ({rate:.0%})",
                success_rate=round(rate, 4), sample_count=total,
                evidence=[f"unit={u_id[:12]}", f"role={r_id[:12]}",
                          f"sample_count={total}", f"rate={rate:.2f}"],
            )
            self._insights[insight.insight_id] = insight
            insights.append(insight)

        return insights

    def get_insights(self, tenant_id: int) -> List[OrgLearningInsight]:
        return [i for i in self._insights.values() if i.tenant_id == tenant_id]

    def get_profile(self, tenant_id: int) -> OrgLearningProfile:
        patterns = []  # Would be filled by cross-reference
        insights = self.get_insights(tenant_id)
        return OrgLearningProfile(
            tenant_id=tenant_id,
            total_patterns=len([p for p in patterns if p.tenant_id == tenant_id]),
            total_profiles=0,
            total_insights=len(insights),
            top_insights=sorted(insights, key=lambda i: i.sample_count, reverse=True)[:5],
        )


# =========================================================================
# 7. Knowledge Evolution
# =========================================================================

class KnowledgeEvolution:
    """Track how learned insights evolve over time.

    Maintains an evolution log for each learning artifact: how confidence,
    success rates, and sample sizes change across updates.
    """

    def __init__(self):
        self._epochs: Dict[str, KnowledgeEpoch] = {}
        self._evolution: List[EvolutionEntry] = []

    def record_update(self, artifact_id: str, tenant_id: int,
                      prev_confidence: float, new_confidence: float,
                      prev_rate: float, new_rate: float,
                      sample_delta: int, reason: str = "") -> EvolutionEntry:
        entry = EvolutionEntry(
            artifact_id=artifact_id, tenant_id=tenant_id,
            previous_confidence=prev_confidence,
            new_confidence=new_confidence,
            previous_success_rate=prev_rate,
            new_success_rate=new_rate,
            sample_delta=sample_delta,
            reason=reason or "periodic update",
        )
        self._evolution.append(entry)
        return entry

    def snapshot_epoch(self, tenant_id: int, label: str,
                       patterns: List[LearnedPattern],
                       profiles: List[OutcomeProfile]) -> KnowledgeEpoch:
        conf_dist: Dict[str, int] = defaultdict(int)
        for p in patterns:
            if p.confidence >= 0.8:
                conf_dist["high"] += 1
            elif p.confidence >= 0.4:
                conf_dist["medium"] += 1
            else:
                conf_dist["low"] += 1
        epoch = KnowledgeEpoch(
            tenant_id=tenant_id, label=label,
            pattern_count=len(patterns),
            profile_count=len(profiles),
            confidence_distribution=dict(conf_dist),
        )
        self._epochs[epoch.epoch_id] = epoch
        return epoch

    def get_history(self, artifact_id: str) -> List[EvolutionEntry]:
        return [e for e in self._evolution if e.artifact_id == artifact_id]

    def get_epochs(self, tenant_id: int) -> List[KnowledgeEpoch]:
        return [e for e in self._epochs.values() if e.tenant_id == tenant_id]


# =========================================================================
# 8. Learning Memory
# =========================================================================

class LearningMemory:
    """Store and query learning artifacts.

    Bounded ring buffer. Supports filtering by type, confidence,
    and tenant. Artifacts are superseded, never deleted.
    """

    def __init__(self, config: Optional[LearnerConfig] = None):
        self._config = config or LearnerConfig()
        self._artifacts: Dict[str, LearningArtifact] = {}
        self._memory: deque[LearningMemoryEntry] = deque(
            maxlen=self._config.learning_memory_size
        )

    def store(self, artifact_type: str, data: Dict[str, Any],
              confidence: float, tenant_id: int,
              evidence: Optional[List[str]] = None) -> LearningArtifact:
        # Supersede previous artifact of same type + signature for tenant
        for existing in self._artifacts.values():
            if (existing.artifact_type == artifact_type
                    and existing.data.get("signature") == data.get("signature")
                    and existing.tenant_id == tenant_id
                    and existing.superseded_at is None):
                existing.superseded_at = datetime.now(timezone.utc).isoformat()

        artifact = LearningArtifact(
            tenant_id=tenant_id, artifact_type=artifact_type,
            data=data, confidence=confidence,
            evidence=evidence or [],
        )
        self._artifacts[artifact.artifact_id] = artifact
        self._memory.append(LearningMemoryEntry(
            artifact_id=artifact.artifact_id, tenant_id=tenant_id,
            artifact_type=artifact_type, confidence=confidence,
            created_at=artifact.created_at,
        ))
        return artifact

    def get_recent(self, tenant_id: Optional[int] = None,
                   artifact_type: Optional[str] = None,
                   min_confidence: Optional[float] = None,
                   limit: int = 50) -> List[LearningArtifact]:
        results = list(self._memory)
        if tenant_id is not None:
            results = [r for r in results if r.tenant_id == tenant_id]
        if artifact_type is not None:
            results = [r for r in results if r.artifact_type == artifact_type]
        if min_confidence is not None:
            results = [r for r in results if r.confidence >= min_confidence]

        artifacts = []
        for entry in reversed(results):
            art = self._artifacts.get(entry.artifact_id)
            if art and art.superseded_at is None:
                artifacts.append(art)
                if len(artifacts) >= limit:
                    break
        return artifacts

    def get_artifact(self, artifact_id: str) -> Optional[LearningArtifact]:
        return self._artifacts.get(artifact_id)

    def size(self) -> int:
        return len(self._memory)

    def capacity(self) -> int:
        return self._config.learning_memory_size


# =========================================================================
# 9. Explainability Layer
# =========================================================================

class ExplainabilityLayer:
    """Explain every learned conclusion with traceable evidence."""

    def explain_pattern(self, pattern: LearnedPattern) -> Dict[str, Any]:
        return {
            "topic": f"Pattern: {pattern.name}",
            "conclusion": f"{pattern.description} (strength={pattern.strength}, confidence={pattern.confidence:.2f})",
            "evidence": pattern.evidence + [
                f"first_observed={pattern.first_observed}",
                f"last_observed={pattern.last_observed}",
                f"observation_count={len(pattern.observation_ids)}",
            ],
            "confidence": pattern.confidence,
        }

    def explain_profile(self, profile: OutcomeProfile) -> Dict[str, Any]:
        return {
            "topic": f"Outcome Profile: {profile.dimension}={profile.dimension_value}",
            "conclusion": f"{profile.successful}/{profile.total_outcomes} successful ({profile.success_rate:.1%})",
            "evidence": [
                f"sample_count={profile.total_outcomes}",
                f"success_rate={profile.success_rate:.4f}",
                f"avg_duration={profile.avg_duration_seconds:.1f}s" if profile.avg_duration_seconds else "no_duration_data",
            ],
            "confidence": min(0.95, profile.total_outcomes / 30),
        }

    def explain_confidence(self, assessment: ConfidenceAssessment) -> Dict[str, Any]:
        return {
            "topic": f"Confidence: {assessment.target_type}/{assessment.target_id[:12]}",
            "conclusion": f"Overall confidence: {assessment.overall:.4f}",
            "evidence": [f"{f.factor}={f.value:.2f} (contrib={f.contribution:.4f})"
                         for f in assessment.factors],
            "confidence": assessment.overall,
        }

    def explain_similarity(self, result: SimilarityResult) -> Dict[str, Any]:
        return {
            "topic": f"Similarity: {result.query_exec_id[:12]}",
            "conclusion": f"Found {len(result.matches)} similar executions from {result.total_candidates} candidates",
            "evidence": [f"{m.target_exec_id[:12]}: score={m.similarity_score:.2f}"
                         for m in result.matches[:5]],
            "confidence": min(0.9, len(result.matches) / 5),
        }


# =========================================================================
# 10. Runtime Service
# =========================================================================

class RuntimeService:
    """Coordination layer for all Learning Intelligence engines."""

    def __init__(self, config: Optional[LearnerConfig] = None):
        self._config = config or LearnerConfig()
        self._patterns = PatternRecognitionEngine(config)
        self._outcomes = OutcomeLearningEngine()
        self._recommendations = RecommendationLearning()
        self._confidence = ConfidenceModel()
        self._similarity = SimilarityEngine()
        self._org_learning = OrganizationalLearning()
        self._evolution = KnowledgeEvolution()
        self._memory = LearningMemory(config)
        self._explain = ExplainabilityLayer()
        self._event_log: List[Dict[str, Any]] = []

    @property
    def patterns(self) -> PatternRecognitionEngine:
        return self._patterns
    @property
    def outcomes(self) -> OutcomeLearningEngine:
        return self._outcomes
    @property
    def recommendations(self) -> RecommendationLearning:
        return self._recommendations
    @property
    def confidence(self) -> ConfidenceModel:
        return self._confidence
    @property
    def similarity(self) -> SimilarityEngine:
        return self._similarity
    @property
    def org_learning(self) -> OrganizationalLearning:
        return self._org_learning
    @property
    def evolution(self) -> KnowledgeEvolution:
        return self._evolution
    @property
    def memory(self) -> LearningMemory:
        return self._memory
    @property
    def explain(self) -> ExplainabilityLayer:
        return self._explain

    # --- Learning from outcomes ---

    def learn_from_outcomes(self, outcomes: List[Dict[str, Any]],
                            tenant_id: int) -> Dict[str, Any]:
        """Process outcomes through all learning engines."""
        patterns = self._patterns.learn(outcomes, tenant_id)
        profiles = self._outcomes.learn(outcomes, tenant_id)
        refinements = self._recommendations.learn(outcomes, tenant_id)
        insights = self._org_learning.learn(outcomes, tenant_id)

        # Store artifacts
        for p in patterns:
            art = self._memory.store(
                LearningCategory.PATTERN.value, p.to_dict(),
                p.confidence, tenant_id,
                evidence=p.evidence,
            )
            self._evolution.record_update(
                artifact_id=art.artifact_id, tenant_id=tenant_id,
                prev_confidence=0.0, new_confidence=p.confidence,
                prev_rate=0.0, new_rate=p.frequency / max(p.frequency, 1),
                sample_delta=p.frequency,
                reason="initial_learning",
            )
        for pr in profiles:
            self._memory.store(
                LearningCategory.OUTCOME_PROFILE.value, pr.to_dict(),
                min(0.95, pr.total_outcomes / 30), tenant_id,
            )

        self._log("learn", patterns=len(patterns), profiles=len(profiles),
                  refinements=len(refinements), tenant_id=tenant_id)

        return {
            "patterns": len(patterns),
            "profiles": len(profiles),
            "refinements": len(refinements),
            "insights": len(insights),
        }

    # --- Queries ---

    def get_patterns(self, tenant_id: int) -> List[LearnedPattern]:
        return self._patterns.get_patterns(tenant_id)

    def get_outcome_profile(self, dim: str, val: str,
                            tenant_id: int) -> Optional[OutcomeProfile]:
        return self._outcomes.get_profile(dim, val, tenant_id)

    def get_refined_recommendation(self, action: str, context: str,
                                   tenant_id: int) -> Optional[RefinedRecommendation]:
        return self._recommendations.get_recommendation(action, context, tenant_id)

    def assess_confidence(self, target_type: str, target_id: str,
                          tenant_id: int, sample_count: int,
                          success_rate: float) -> ConfidenceAssessment:
        return self._confidence.assess(
            target_type, target_id, tenant_id,
            sample_count, success_rate,
        )

    def find_similar(self, exec_data: Dict[str, Any],
                     candidates: List[Dict[str, Any]],
                     tenant_id: int) -> SimilarityResult:
        return self._similarity.find_similar(exec_data, candidates, tenant_id)

    def get_org_profile(self, tenant_id: int) -> OrgLearningProfile:
        return self._org_learning.get_profile(tenant_id)

    def snapshot_epoch(self, tenant_id: int, label: str) -> KnowledgeEpoch:
        return self._evolution.snapshot_epoch(
            tenant_id, label,
            self._patterns.get_patterns(tenant_id),
            self._outcomes.get_profiles(tenant_id),
        )

    def get_recent_artifacts(self, tenant_id: Optional[int] = None,
                             artifact_type: Optional[str] = None,
                             min_confidence: Optional[float] = None,
                             limit: int = 50) -> List[LearningArtifact]:
        return self._memory.get_recent(tenant_id, artifact_type, min_confidence, limit)

    def explain_pattern(self, pattern_id: str) -> Dict[str, Any]:
        p = self._patterns.get_pattern(pattern_id)
        if not p:
            return {"error": "pattern_not_found"}
        return self._explain.explain_pattern(p)

    def explain_profile(self, dim: str, val: str, tenant_id: int) -> Dict[str, Any]:
        p = self._outcomes.get_profile(dim, val, tenant_id)
        if not p:
            return {"error": "profile_not_found"}
        return self._explain.explain_profile(p)

    def stats(self) -> Dict[str, Any]:
        s = LearnerStats(
            total_patterns=len(self._patterns._patterns),
            total_profiles=len(self._outcomes._profiles),
            total_recommendations=len(self._recommendations._recommendations),
            total_assessments=0,
            total_insights=len(self._org_learning._insights),
            total_artifacts=len(self._memory._artifacts),
            memory_utilization_pct=(self._memory.size() / max(self._memory.capacity(), 1)) * 100,
        )
        return s.to_dict()

    def _log(self, event: str, **kw) -> None:
        self._event_log.append({
            "event": event, **kw,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# =========================================================================
# Facade
# =========================================================================

class LearningIntelligenceEngine:
    """Facade over all Learning Intelligence components.

    Usage:
        li = LearningIntelligenceEngine()
        result = li.learn_from_outcomes(outcomes, tenant_id)
        patterns = li.get_patterns(tenant_id)
    """

    def __init__(self, config: Optional[LearnerConfig] = None):
        self._runtime = RuntimeService(config)

    @property
    def runtime(self) -> RuntimeService:
        return self._runtime

    def learn_from_outcomes(self, outcomes: List[Dict[str, Any]],
                            tenant_id: int) -> Dict[str, Any]:
        return self._runtime.learn_from_outcomes(outcomes, tenant_id)

    def get_patterns(self, tenant_id: int) -> List[LearnedPattern]:
        return self._runtime.get_patterns(tenant_id)

    def get_outcome_profile(self, dim: str, val: str,
                            tenant_id: int) -> Optional[OutcomeProfile]:
        return self._runtime.get_outcome_profile(dim, val, tenant_id)

    def assess_confidence(self, target_type: str, target_id: str,
                          tenant_id: int, sample_count: int,
                          success_rate: float) -> ConfidenceAssessment:
        return self._runtime.assess_confidence(
            target_type, target_id, tenant_id, sample_count, success_rate)

    def find_similar(self, exec_data: Dict[str, Any],
                     candidates: List[Dict[str, Any]],
                     tenant_id: int) -> SimilarityResult:
        return self._runtime.find_similar(exec_data, candidates, tenant_id)

    def get_org_profile(self, tenant_id: int) -> OrgLearningProfile:
        return self._runtime.get_org_profile(tenant_id)

    def snapshot_epoch(self, tenant_id: int, label: str) -> KnowledgeEpoch:
        return self._runtime.snapshot_epoch(tenant_id, label)

    def get_recent_artifacts(self, tenant_id: Optional[int] = None,
                             artifact_type: Optional[str] = None,
                             min_confidence: Optional[float] = None,
                             limit: int = 50) -> List[LearningArtifact]:
        return self._runtime.get_recent_artifacts(
            tenant_id, artifact_type, min_confidence, limit)

    def explain_pattern(self, pattern_id: str) -> Dict[str, Any]:
        return self._runtime.explain_pattern(pattern_id)

    def stats(self) -> Dict[str, Any]:
        return self._runtime.stats()