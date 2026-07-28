"""SHUNYA Learning Engine — pattern extraction and knowledge consolidation.

The Learning Engine extracts patterns from outcomes and reflections,
consolidates them into Knowledge, and improves future reasoning.
All learning is deterministic — no AI escalation.
"""

from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone
from typing import Any

from core.intelligence.models import (
    EngineInput,
    EngineOutput,
    Pattern,
    ReflectionRecord,
)


class LearningEngine:
    """Extract patterns from outcomes, consolidate into knowledge.

    All learning is deterministic. No AI escalation.
    """

    def __init__(self):
        self.engine_id = "learning_engine"
        self.engine_type = "learning"
        self._patterns: dict[str, Pattern] = {}
        self._reflection_log: list[ReflectionRecord] = []
        self._success_history: list[float] = []

    # ── Public Interface ─────────────────────────────────────────────

    def process(self, input_data: EngineInput) -> EngineOutput:
        """Process a reflection record or batch and extract patterns.

        Args:
            input_data: EngineInput with input_type="reflection" or "batch"
                        payload containing reflection records.

        Returns:
            EngineOutput with detected patterns.
        """
        t0 = time.time()
        trace_id = input_data.trace_id

        if input_data.input_type == "reflection":
            records = [ReflectionRecord(**input_data.payload)]
        elif input_data.input_type == "batch":
            records = [ReflectionRecord(**r) for r in input_data.payload.get("records", [])]
        else:
            return EngineOutput(
                output_type="error",
                payload={"error": f"Unknown input type: {input_data.input_type}"},
                confidence=0.0, deterministic=True, trace_id=trace_id,
                processing_time_ms=(time.time() - t0) * 1000,
            )

        patterns = []
        for record in records:
            self._reflection_log.append(record)
            self._success_history.append(record.success_score)
            detected = self._detect_patterns(record)
            for p in detected:
                self._patterns[p.pattern_id] = p
            patterns.extend(detected)

        # Consolidate patterns (merge similar)
        consolidated = self._consolidate_patterns(patterns)

        # Adjust confidence weights based on accuracy
        weight_adjustments = self._compute_weight_adjustments()

        return EngineOutput(
            output_type="patterns_detected",
            payload={
                "patterns": [self._pattern_to_dict(p) for p in consolidated],
                "total_patterns": len(consolidated),
                "total_reflections": len(self._reflection_log),
                "weight_adjustments": weight_adjustments,
            },
            confidence=min(0.95, len(consolidated) / max(len(patterns), 1) * 0.9),
            deterministic=True,
            trace_id=trace_id,
            processing_time_ms=(time.time() - t0) * 1000,
        )

    def escalate(self, input_data: EngineInput) -> Any:
        """Learning Engine never escalates. All learning is deterministic."""
        return self.process(input_data)

    def get_capabilities(self) -> list[str]:
        return [
            "pattern_detection", "knowledge_consolidation",
            "confidence_adjustment", "success_tracking",
        ]

    def health_check(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "status": "active",
            "total_patterns": len(self._patterns),
            "total_reflections": len(self._reflection_log),
            "avg_success": self._average_success(),
        }

    # ── Pattern Detection ────────────────────────────────────────────

    def _detect_patterns(self, record: ReflectionRecord) -> list[Pattern]:
        """Detect patterns from a single reflection record."""
        patterns = []

        # Pattern: recurring improvement signal
        for signal in record.improvement_signals:
            sig_type = signal.get("type", "unknown")
            existing = self._find_pattern_by_type(sig_type)
            if existing:
                existing.support_count += 1
                existing.last_observed = datetime.now(timezone.utc).isoformat()
                existing.confidence = min(0.99, existing.confidence + 0.05)
            else:
                p = Pattern(
                    pattern_type=sig_type,
                    description=signal.get("description", ""),
                    confidence=0.3,
                    support_count=1,
                )
                patterns.append(p)

        # Pattern: low success trend
        if record.success_score < 0.3:
            p = Pattern(
                pattern_type="low_success",
                description=f"Low success score: {record.success_score}",
                confidence=0.4,
                support_count=1,
            )
            patterns.append(p)

        # Pattern: anomaly recurrence
        for anomaly in record.anomalies:
            existing = self._find_pattern_by_desc(anomaly)
            if existing:
                existing.support_count += 1
                existing.confidence = min(0.99, existing.confidence + 0.1)

        return patterns

    def _find_pattern_by_type(self, pattern_type: str) -> Pattern | None:
        for p in self._patterns.values():
            if p.pattern_type == pattern_type:
                return p
        return None

    def _find_pattern_by_desc(self, description: str) -> Pattern | None:
        for p in self._patterns.values():
            if description in p.description:
                return p
        return None

    def _consolidate_patterns(self, patterns: list[Pattern]) -> list[Pattern]:
        """Merge duplicate patterns and update confidence."""
        merged: dict[str, Pattern] = {}
        for p in patterns:
            key = f"{p.pattern_type}:{p.description[:50]}"
            if key in merged:
                merged[key].support_count += p.support_count
                merged[key].confidence = min(0.99, merged[key].confidence + 0.05)
            else:
                merged[key] = p
        return list(merged.values())

    def _compute_weight_adjustments(self) -> dict[str, Any]:
        """Adjust confidence weights based on prediction accuracy."""
        if len(self._success_history) < 5:
            return {"adjusted": False, "reason": "insufficient_data"}

        recent = self._success_history[-20:]
        mean = statistics.mean(recent)
        stdev = statistics.stdev(recent) if len(recent) > 1 else 0.1

        return {
            "adjusted": True,
            "mean_success": round(mean, 3),
            "std_dev": round(stdev, 3),
            "trend": "improving" if len(recent) > 5 and recent[-1] > recent[0] else "stable",
        }

    def _average_success(self) -> float:
        if not self._success_history:
            return 0.0
        return round(sum(self._success_history) / len(self._success_history), 3)

    def _pattern_to_dict(self, p: Pattern) -> dict[str, Any]:
        return {
            "pattern_id": p.pattern_id,
            "pattern_type": p.pattern_type,
            "description": p.description,
            "confidence": p.confidence,
            "support_count": p.support_count,
        }

    def get_patterns(self) -> list[Pattern]:
        return list(self._patterns.values())

    def clear(self) -> None:
        self._patterns.clear()
        self._reflection_log.clear()
        self._success_history.clear()