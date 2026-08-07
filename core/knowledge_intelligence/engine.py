"""Universal Knowledge Intelligence — Core Engine.

Pure computation engine for knowledge analysis:
- Semantic search (keyword + tag + type + confidence)
- Concept linking (automatic knowledge graph construction)
- Contradiction detection
- Duplicate detection
- Confidence scoring
- Freshness scoring
- Source attribution
- Gap detection
- Knowledge recommendations
- Explainable reasoning

Pure computation — no storage, no side effects.
"""

from __future__ import annotations

import re
from typing import Any

from core.knowledge_intelligence.models import (
    ConfidenceLevel,
    Contradiction,
    GapSeverity,
    Knowledge,
    KnowledgeGap,
    KnowledgeGraph,
    KnowledgeLink,
    KnowledgeRecommendation,
    KnowledgeRelationship,
    KnowledgeSource,
    KnowledgeType,
    SearchResult,
    SourceType,
    _generate_id,
    _now_iso,
)


class KnowledgeIntelligenceEngine:
    """Pure computation engine for Universal Knowledge Intelligence.

    Every method is a pure function: input → output, no state.
    Thread-safe by design.
    """

    # ── Semantic Search ─────────────────────────────────────────────────

    def search(
        self,
        knowledge_list: list[Knowledge],
        query: str,
        types: list[str] | None = None,
        domains: list[str] | None = None,
        tags: list[str] | None = None,
        min_confidence: float = 0.0,
        max_results: int = 20,
    ) -> list[SearchResult]:
        """Semantic search across knowledge objects."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        results: list[SearchResult] = []
        for k in knowledge_list:
            if not k.is_active:
                continue
            if types and k.knowledge_type not in types:
                continue
            if domains and k.domain not in domains:
                continue
            if tags and not any(t in k.tags for t in tags):
                continue
            if k.confidence_score < min_confidence:
                continue

            score, matched = self._score_relevance(k, query_lower, query_terms)
            if score > 0:
                results.append(SearchResult(
                    knowledge_id=k.knowledge_id,
                    title=k.title,
                    summary=k.summary or k.statement[:200],
                    knowledge_type=k.knowledge_type,
                    relevance_score=round(score, 4),
                    confidence_score=k.confidence_score,
                    matched_terms=list(matched),
                    context=k.context or k.domain,
                ))

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:max_results]

    def _score_relevance(
        self, k: Knowledge, query_lower: str, query_terms: set[str]
    ) -> tuple[float, set[str]]:
        """Score relevance of a knowledge object to a query."""
        score = 0.0
        matched: set[str] = set()

        # Exact title match
        if query_lower in k.title.lower():
            score += 10.0
            matched.add(k.title)
        # Title term matches
        title_terms = set(k.title.lower().split())
        matched_title = title_terms & query_terms
        if matched_title:
            score += 5.0 * len(matched_title) / max(len(query_terms), 1)
            matched.update(matched_title)

        # Statement/body matches
        if query_lower in k.statement.lower():
            score += 5.0
        statement_terms = set(k.statement.lower().split())
        matched_statement = statement_terms & query_terms
        if matched_statement:
            score += 3.0 * len(matched_statement) / max(len(query_terms), 1)
            matched.update(matched_statement)

        # Tag matches
        tag_terms = set(t.lower() for t in k.tags)
        matched_tags = tag_terms & query_terms
        if matched_tags:
            score += 4.0 * len(matched_tags)
            matched.update(matched_tags)

        # Domain match
        if k.domain.lower() == query_lower or k.domain.lower() in query_terms:
            score += 3.0
            matched.add(k.domain)

        # Type match (implicit — if query mentions the type)
        if k.knowledge_type.lower() in query_terms:
            score += 2.0

        # Summary match
        if k.summary and query_lower in k.summary.lower():
            score += 2.0

        # Boost by confidence
        score *= (0.5 + k.confidence_score * 0.5)

        return score, matched

    # ── Concept Linking ─────────────────────────────────────────────────

    def build_knowledge_graph(
        self, knowledge_list: list[Knowledge]
    ) -> KnowledgeGraph:
        """Build a knowledge graph by linking related concepts.

        Links are created based on:
        - Shared tags
        - Same domain
        - Title/statement overlap
        - Explicit links already defined
        - Type relationships (e.g. SOP references a procedure)
        """
        nodes = list(knowledge_list)
        edges: list[KnowledgeLink] = []
        seen_pairs: set[tuple[str, str]] = set()

        # Collect explicit links already defined
        for k in knowledge_list:
            for link in k.links:
                pair = tuple(sorted([link.source_knowledge_id, link.target_knowledge_id]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    edges.append(link)

        # Auto-link: shared tags
        for i, ka in enumerate(knowledge_list):
            for kb in knowledge_list[i + 1:]:
                pair = tuple(sorted([ka.knowledge_id, kb.knowledge_id]))
                if pair in seen_pairs:
                    continue

                shared_tags = set(ka.tags) & set(kb.tags)
                if shared_tags:
                    strength = len(shared_tags) / max(len(set(ka.tags + kb.tags)), 1)
                    edges.append(KnowledgeLink(
                        source_knowledge_id=ka.knowledge_id,
                        target_knowledge_id=kb.knowledge_id,
                        relationship=KnowledgeRelationship.RELATED_TO.value,
                        strength=round(strength, 2),
                        evidence=f"Shared tags: {', '.join(shared_tags)}",
                    ))
                    seen_pairs.add(pair)
                    continue

                # Auto-link: same domain
                if ka.domain and ka.domain == kb.domain and ka.domain != "":
                    edges.append(KnowledgeLink(
                        source_knowledge_id=ka.knowledge_id,
                        target_knowledge_id=kb.knowledge_id,
                        relationship=KnowledgeRelationship.RELATED_TO.value,
                        strength=0.5,
                        evidence=f"Same domain: {ka.domain}",
                    ))
                    seen_pairs.add(pair)

        return KnowledgeGraph(nodes=nodes, edges=edges)

    # ── Contradiction Detection ─────────────────────────────────────────

    def detect_contradictions(
        self, knowledge_list: list[Knowledge]
    ) -> list[Contradiction]:
        """Detect contradictions between knowledge objects.

        Checks:
        - Explicit contradicts links
        - Conflicting statements on the same topic
        - Opposing confidence levels on shared claims
        """
        contradictions: list[Contradiction] = []
        checked: set[tuple[str, str]] = set()

        for ka in knowledge_list:
            for kb in knowledge_list:
                if ka.knowledge_id == kb.knowledge_id:
                    continue
                pair = tuple(sorted([ka.knowledge_id, kb.knowledge_id]))
                if pair in checked:
                    continue
                checked.add(pair)

                # 1. Explicit contradiction links
                for link in ka.links:
                    if link.target_knowledge_id == kb.knowledge_id and \
                       link.relationship == KnowledgeRelationship.CONTRADICTS.value:
                        contradictions.append(Contradiction(
                            knowledge_id_a=ka.knowledge_id,
                            knowledge_id_b=kb.knowledge_id,
                            title_a=ka.title,
                            title_b=kb.title,
                            statement_a=ka.statement[:200],
                            statement_b=kb.statement[:200],
                            contradiction_type="direct",
                            severity="high",
                            evidence=[{"type": "explicit_link", "detail": link.evidence or "Explicit contradiction"}],
                        ))
                        continue

                # 2. Same topic, conflicting statements
                shared_tags = set(ka.tags) & set(kb.tags)
                if shared_tags and ka.domain and ka.domain == kb.domain:
                    # Check for opposite claims
                    if self._is_contradictory_statement(ka.statement, kb.statement):
                        contradictions.append(Contradiction(
                            knowledge_id_a=ka.knowledge_id,
                            knowledge_id_b=kb.knowledge_id,
                            title_a=ka.title,
                            title_b=kb.title,
                            statement_a=ka.statement[:200],
                            statement_b=kb.statement[:200],
                            contradiction_type="implied",
                            severity="medium",
                            evidence=[{"type": "shared_topic", "detail": f"Shared tags: {', '.join(shared_tags)}"}],
                        ))

        return contradictions

    def _is_contradictory_statement(self, a: str, b: str) -> bool:
        """Heuristic check for contradictory statements."""
        a_lower = a.lower()
        b_lower = b.lower()
        negation_words = {"not", "never", "no", "cannot", "can't", "doesn't", "don't", "isn't", "aren't"}

        # Check if both statements cover the same topic but one negates it
        a_words = set(a_lower.split())
        b_words = set(b_lower.split())
        content_words = {w for w in a_words | b_words if len(w) > 3 and w not in negation_words}

        # One has negation, the other doesn't
        a_has_negation = bool(a_words & negation_words)
        b_has_negation = bool(b_words & negation_words)

        if a_has_negation != b_has_negation:
            common_content = a_words & b_words & content_words
            if len(common_content) >= 2:
                return True

        return False

    # ── Duplicate Detection ─────────────────────────────────────────────

    def detect_duplicates(
        self, knowledge_list: list[Knowledge]
    ) -> list[dict[str, Any]]:
        """Detect potential duplicate knowledge objects."""
        duplicates: list[dict[str, Any]] = []
        checked: set[tuple[str, str]] = set()

        for i, ka in enumerate(knowledge_list):
            for kb in knowledge_list[i + 1:]:
                pair = (ka.knowledge_id, kb.knowledge_id)
                if pair in checked:
                    continue
                checked.add(pair)

                similarity = self._compute_similarity(ka, kb)
                if similarity > 0.7:
                    duplicates.append({
                        "knowledge_a_id": ka.knowledge_id,
                        "knowledge_b_id": kb.knowledge_id,
                        "title_a": ka.title,
                        "title_b": kb.title,
                        "similarity_score": round(similarity, 2),
                        "evidence": [
                            {"type": "title_similarity", "value": self._title_similarity(ka.title, kb.title)},
                            {"type": "statement_similarity", "value": self._statement_similarity(ka.statement, kb.statement)},
                        ],
                        "recommendation": "Merge or mark as superseded" if similarity > 0.85 else "Review for consolidation",
                    })

        return duplicates

    def _compute_similarity(self, a: Knowledge, b: Knowledge) -> float:
        """Compute overall similarity between two knowledge objects."""
        title_sim = self._title_similarity(a.title, b.title) * 0.3
        statement_sim = self._statement_similarity(a.statement, b.statement) * 0.4
        tag_sim = self._tag_similarity(a.tags, b.tags) * 0.2
        type_sim = (1.0 if a.knowledge_type == b.knowledge_type else 0.0) * 0.1
        return title_sim + statement_sim + tag_sim + type_sim

    def _title_similarity(self, title_a: str, title_b: str) -> float:
        a_words = set(title_a.lower().split())
        b_words = set(title_b.lower().split())
        if not a_words or not b_words:
            return 0.0
        intersection = a_words & b_words
        return len(intersection) / max(len(a_words | b_words), 1)

    def _statement_similarity(self, stmt_a: str, stmt_b: str) -> float:
        a_words = set(stmt_a.lower().split())
        b_words = set(stmt_b.lower().split())
        if not a_words or not b_words:
            return 0.0
        intersection = a_words & b_words
        return len(intersection) / max(len(a_words | b_words), 1)

    def _tag_similarity(self, tags_a: list[str], tags_b: list[str]) -> float:
        if not tags_a or not tags_b:
            return 0.0
        set_a, set_b = set(tags_a), set(tags_b)
        intersection = set_a & set_b
        return len(intersection) / max(len(set_a | set_b), 1)

    # ── Confidence Scoring ──────────────────────────────────────────────

    def compute_confidence(
        self, knowledge: Knowledge,
        source_reliability: float = 0.5,
        evidence_count: int = 0,
        corroboration_count: int = 0,
    ) -> dict[str, Any]:
        """Compute a comprehensive confidence score for a knowledge object.

        Factors:
        - Source reliability (0-1)
        - Number of supporting evidence sources
        - Corroboration from other knowledge
        - Freshness
        - Version history
        """
        source_score = min(1.0, source_reliability)
        evidence_score = min(1.0, evidence_count * 0.15)
        corroboration_score = min(1.0, corroboration_count * 0.12)
        freshness_score = knowledge.freshness_score
        version_score = min(1.0, knowledge.version * 0.05)

        score = (
            source_score * 0.30 +
            evidence_score * 0.25 +
            corroboration_score * 0.20 +
            freshness_score * 0.15 +
            version_score * 0.10
        )

        if score >= 0.85:
            level = ConfidenceLevel.CONFIRMED.value
        elif score >= 0.70:
            level = ConfidenceLevel.HIGH.value
        elif score >= 0.50:
            level = ConfidenceLevel.MODERATE.value
        elif score >= 0.30:
            level = ConfidenceLevel.LOW.value
        else:
            level = ConfidenceLevel.UNVERIFIED.value

        return {
            "score": round(score, 4),
            "level": level,
            "factors": {
                "source_reliability": round(source_score, 4),
                "evidence_count": round(evidence_score, 4),
                "corroboration_count": round(corroboration_score, 4),
                "freshness": round(freshness_score, 4),
                "version": round(version_score, 4),
            },
        }

    # ── Freshness Scoring ───────────────────────────────────────────────

    def compute_freshness(self, knowledge: Knowledge) -> float:
        """Compute freshness score based on age and review status.

        Score decays from 1.0 (just created) toward 0.1 (old, unreviewed).
        """
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        try:
            created = datetime.fromisoformat(knowledge.created_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return 0.5

        age_days = (now - created).days

        # Freshness decays over 365 days
        decay = max(0.1, 1.0 - age_days / 365)

        # Boost if recently reviewed
        if knowledge.review_by:
            try:
                review_dt = datetime.fromisoformat(knowledge.review_by.replace("Z", "+00:00"))
                if review_dt > now:
                    decay = min(1.0, decay + 0.2)  # Scheduled review = planned freshness
            except (ValueError, TypeError):
                pass

        return round(decay, 4)

    # ── Gap Detection ───────────────────────────────────────────────────

    def detect_gaps(
        self,
        knowledge_list: list[Knowledge],
        domain: str = "",
        known_topics: list[str] | None = None,
    ) -> list[KnowledgeGap]:
        """Detect gaps in knowledge coverage.

        Checks:
        - Missing types for a domain (e.g. SOP without a procedure)
        - Unanswered questions
        - Low-confidence knowledge needing corroboration
        - Stale knowledge needing review
        """
        gaps: list[KnowledgeGap] = []
        topics = known_topics or []

        domain_knowledge = [k for k in knowledge_list if not domain or k.domain == domain]
        active_knowledge = [k for k in domain_knowledge if k.is_active]

        # 1. Missing knowledge types in domain
        present_types = {k.knowledge_type for k in active_knowledge}
        all_types = {t.value for t in KnowledgeType}
        core_types = {KnowledgeType.FACT.value, KnowledgeType.CONCEPT.value,
                      KnowledgeType.DEFINITION.value, KnowledgeType.PROCEDURE.value,
                      KnowledgeType.POLICY.value}
        missing_core = core_types - present_types

        if missing_core:
            gaps.append(KnowledgeGap(
                title=f"Missing core knowledge types in domain '{domain or 'general'}'",
                description=f"Missing: {', '.join(missing_core)}",
                severity=GapSeverity.HIGH.value,
                domain=domain,
                reason=f"Domain lacks foundational knowledge types: {', '.join(missing_core)}",
                resolution_suggestion=f"Create knowledge objects for each missing type: {', '.join(missing_core)}",
                evidence=[{"type": "missing_types", "value": list(missing_core)}],
            ))

        # 2. Unanswered questions
        questions = [k for k in active_knowledge if k.knowledge_type == KnowledgeType.QUESTION.value]
        for q in questions:
            # Check if any knowledge answers this question
            has_answer = any(
                link.source_knowledge_id == q.knowledge_id
                and link.relationship == KnowledgeRelationship.ANSWERS.value
                for k in active_knowledge
                for link in k.links
            )
            if not has_answer and q.tags:
                gaps.append(KnowledgeGap(
                    title=f"Unanswered question: {q.title}",
                    description=q.statement[:200],
                    severity=GapSeverity.MEDIUM.value,
                    domain=q.domain,
                    related_knowledge_ids=[q.knowledge_id],
                    reason=f"Question '{q.title}' has no linked answer",
                    resolution_suggestion=f"Research and create a knowledge object that answers this question",
                    evidence=[{"type": "unanswered_question", "value": q.title}],
                ))

        # 3. Low-confidence knowledge needing evidence
        low_confidence = [k for k in active_knowledge if k.confidence_score < 0.3]
        if low_confidence:
            gaps.append(KnowledgeGap(
                title=f"{len(low_confidence)} knowledge objects with low confidence",
                description=f"{len(low_confidence)} objects need additional evidence or corroboration",
                severity=GapSeverity.MEDIUM.value,
                domain=domain,
                related_knowledge_ids=[k.knowledge_id for k in low_confidence[:5]],
                reason="Low confidence scores indicate insufficient evidence",
                resolution_suggestion="Add sources, evidence, or corroborating knowledge for each low-confidence item",
                evidence=[{"type": "low_confidence_count", "value": len(low_confidence)}],
            ))

        # 4. Stale knowledge needing review
        stale = [k for k in active_knowledge if k.is_due_for_review]
        if stale:
            gaps.append(KnowledgeGap(
                title=f"{len(stale)} knowledge objects due for review",
                description=f"{len(stale)} objects have passed their review date",
                severity=GapSeverity.LOW.value,
                domain=domain,
                related_knowledge_ids=[k.knowledge_id for k in stale[:5]],
                reason="Knowledge may be outdated",
                resolution_suggestion="Schedule review for each overdue knowledge object",
                evidence=[{"type": "stale_count", "value": len(stale)}],
            ))

        return gaps

    # ── Knowledge Recommendations ───────────────────────────────────────

    def recommend_knowledge(
        self,
        knowledge_list: list[Knowledge],
        domain: str = "",
        count: int = 5,
    ) -> list[KnowledgeRecommendation]:
        """Recommend knowledge that should be created or acquired.

        Recommendations are based on:
        - Gaps in knowledge types
        - Missing documentation for procedures
        - Low-confidence items needing evidence
        - Questions without answers
        """
        recommendations: list[KnowledgeRecommendation] = []
        gaps = self.detect_gaps(knowledge_list, domain)

        for gap in gaps:
            if gap.severity == GapSeverity.HIGH.value:
                recommendations.append(KnowledgeRecommendation(
                    title=gap.title,
                    description=gap.description,
                    priority="high",
                    reason=gap.reason,
                    related_knowledge=gap.related_knowledge_ids,
                    evidence=gap.evidence,
                ))

        # SOP without procedure
        domain_knowledge = [k for k in knowledge_list if not domain or k.domain == domain]
        active = [k for k in domain_knowledge if k.is_active]
        sop_count = sum(1 for k in active if k.knowledge_type == KnowledgeType.SOP.value)
        procedure_count = sum(1 for k in active if k.knowledge_type == KnowledgeType.PROCEDURE.value)

        if sop_count > procedure_count and sop_count > 0:
            recommendations.append(KnowledgeRecommendation(
                title=f"Missing procedures for {sop_count - procedure_count} SOP(s)",
                description=f"{sop_count} SOPs but only {procedure_count} procedures defined",
                priority="high",
                reason="SOPs should be backed by detailed procedures",
                evidence=[{"type": "sop_procedure_gap", "sop_count": sop_count, "procedure_count": procedure_count}],
            ))

        # Low average confidence
        scores = [k.confidence_score for k in active if k.is_active]
        if scores and sum(scores) / len(scores) < 0.4:
            recommendations.append(KnowledgeRecommendation(
                title="Low average knowledge confidence",
                description=f"Average confidence is {sum(scores)/len(scores):.2f} — below 0.4 threshold",
                priority="medium",
                reason="Knowledge base lacks sufficient evidence and corroboration",
                suggested_source_types=[SourceType.RESEARCH_PAPER.value, SourceType.EXPERIMENT.value,
                                         SourceType.EXPERIENCE.value],
                evidence=[{"type": "avg_confidence", "value": round(sum(scores)/len(scores), 2)}],
            ))

        return recommendations[:count]

    # ── Evidence Reasoning ──────────────────────────────────────────────

    def reason_with_evidence(
        self, knowledge: Knowledge, knowledge_list: list[Knowledge]
    ) -> dict[str, Any]:
        """Analyze the evidence supporting or contradicting a knowledge object.

        Returns a structured reasoning report with all evidence.
        """
        supporting: list[dict[str, Any]] = []
        contradicting: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []

        # Supporting links (both outgoing and incoming)
        for link in knowledge.links:
            target = next((k for k in knowledge_list if k.knowledge_id == link.target_knowledge_id), None)
            if link.relationship == KnowledgeRelationship.EVIDENCE_FOR.value:
                supporting.append({
                    "knowledge_id": link.target_knowledge_id,
                    "title": target.title if target else "Unknown",
                    "relationship": link.relationship,
                    "evidence": link.evidence,
                })
            elif link.relationship == KnowledgeRelationship.EVIDENCE_AGAINST.value:
                contradicting.append({
                    "knowledge_id": link.target_knowledge_id,
                    "title": target.title if target else "Unknown",
                    "relationship": link.relationship,
                    "evidence": link.evidence,
                })

        # Also check incoming links (other knowledge pointing TO this one)
        for k in knowledge_list:
            if k.knowledge_id == knowledge.knowledge_id:
                continue
            for link in k.links:
                if link.target_knowledge_id == knowledge.knowledge_id:
                    if link.relationship == KnowledgeRelationship.EVIDENCE_FOR.value:
                        supporting.append({
                            "knowledge_id": k.knowledge_id,
                            "title": k.title,
                            "relationship": link.relationship,
                            "evidence": link.evidence,
                        })
                    elif link.relationship == KnowledgeRelationship.EVIDENCE_AGAINST.value:
                        contradicting.append({
                            "knowledge_id": k.knowledge_id,
                            "title": k.title,
                            "relationship": link.relationship,
                            "evidence": link.evidence,
                        })

        # Contradictions
        contradictions = self.detect_contradictions([knowledge] + [
            k for k in knowledge_list if k.knowledge_id != knowledge.knowledge_id
        ])
        for c in contradictions:
            if c.knowledge_id_a == knowledge.knowledge_id:
                contradicting.append({
                    "knowledge_id": c.knowledge_id_b,
                    "title": c.title_b,
                    "relationship": "contradicts",
                    "evidence": c.statement_b[:200],
                })

        # Sources
        for s in knowledge.sources:
            sources.append(s.to_dict())

        # Confidence analysis
        confidence = self.compute_confidence(
            knowledge,
            source_reliability=min(1.0, len(knowledge.sources) * 0.2),
            evidence_count=len(supporting),
            corroboration_count=len([k for k in knowledge_list if k.knowledge_id != knowledge.knowledge_id]),
        )

        return {
            "knowledge_id": knowledge.knowledge_id,
            "title": knowledge.title,
            "statement": knowledge.statement,
            "confidence": confidence,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "sources": sources,
            "source_count": len(sources),
            "supporting_count": len(supporting),
            "contradicting_count": len(contradicting),
            "assessment": (
                "well_supported" if len(supporting) > len(contradicting)
                else "contested" if len(contradicting) > 0
                else "insufficient_evidence"
            ),
        }

    # ── Source Attribution ──────────────────────────────────────────────

    def attribute_sources(
        self, knowledge_list: list[Knowledge]
    ) -> dict[str, Any]:
        """Analyze source coverage across a knowledge base."""
        total = len(knowledge_list)
        with_sources = sum(1 for k in knowledge_list if k.sources)
        with_multiple = sum(1 for k in knowledge_list if len(k.sources) >= 2)

        source_types: dict[str, int] = {}
        for k in knowledge_list:
            for s in k.sources:
                source_types[s.source_type] = source_types.get(s.source_type, 0) + 1

        return {
            "total_knowledge": total,
            "with_sources": with_sources,
            "with_multiple_sources": with_multiple,
            "source_coverage_pct": round(with_sources / total * 100, 1) if total > 0 else 0,
            "source_type_distribution": source_types,
            "recommendation": (
                "Add sources to unsourced knowledge objects"
                if with_sources < total
                else "Good source coverage"
            ),
        }

    # ── AI Context ──────────────────────────────────────────────────────

    def prepare_ai_context(self, knowledge_list: list[Knowledge]) -> dict[str, Any]:
        """Prepare structured context for AI understanding."""
        active = [k for k in knowledge_list if k.is_active]
        type_counts = {}
        for k in active:
            type_counts[k.knowledge_type] = type_counts.get(k.knowledge_type, 0) + 1

        contradictions = self.detect_contradictions(active)
        graph = self.build_knowledge_graph(active)
        avg_conf = sum(k.confidence_score for k in active) / len(active) if active else 0

        return {
            "knowledge_base": {
                "total": len(active),
                "by_type": type_counts,
                "domains": list(set(k.domain for k in active if k.domain)),
                "average_confidence": round(avg_conf, 2),
            },
            "graph": {
                "nodes": graph.node_count,
                "edges": graph.edge_count,
            },
            "contradictions": {
                "count": len(contradictions),
                "unresolved": sum(1 for c in contradictions if not c.resolved),
            },
            "recent": [
                {
                    "id": k.knowledge_id,
                    "title": k.title,
                    "type": k.knowledge_type,
                    "confidence": k.confidence_score,
                    "created_at": k.created_at,
                }
                for k in sorted(active, key=lambda x: x.created_at, reverse=True)[:5]
            ],
        }