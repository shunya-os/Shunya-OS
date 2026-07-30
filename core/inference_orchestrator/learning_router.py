"""Learning Router — telemetry recording, routing recommendations, and insights.

The Learning Router observes every inference request, records outcomes
(provider, latency, token usage, success/failure), and evolves routing
recommendations over time so the orchestrator learns which providers
perform best for which request patterns.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ── Data Types ──────────────────────────────────────────────────────────────


@dataclass
class TelemetryRecord:
    """A single observed inference request."""
    session_id: str = ""
    provider: str = ""
    model: str = ""
    request_type: str = "chat"            # "chat", "embedding", "tool_call", etc.
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: str | None = None
    finish_reason: str = "stop"
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "request_type": self.request_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": round(self.latency_ms, 1),
            "success": self.success,
            "error": self.error,
            "finish_reason": self.finish_reason,
            "timestamp": self.timestamp,
        }


@dataclass
class ProviderScore:
    """Aggregated performance score for a provider/model combination."""
    provider: str
    model: str
    total_requests: int = 0
    successful_requests: int = 0
    avg_latency_ms: float = 0.0
    avg_input_tokens: int = 0
    avg_output_tokens: int = 0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    error_rate: float = 0.0
    score: float = 0.0          # Composite score (higher = better)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "error_rate": round(self.error_rate, 3),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "p50_latency_ms": round(self.p50_latency_ms, 1),
            "p95_latency_ms": round(self.p95_latency_ms, 1),
            "avg_input_tokens": self.avg_input_tokens,
            "avg_output_tokens": self.avg_output_tokens,
            "score": round(self.score, 3),
        }


@dataclass
class Recommendation:
    """A routing recommendation from the Learning Router."""
    provider: str
    model: str
    confidence: float = 0.0
    reason: str = ""
    alternatives: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
            "alternatives": self.alternatives,
        }


# ── Learning Router ─────────────────────────────────────────────────────────


class LearningRouter:
    """Records telemetry and improves routing recommendations.

    Stores observation data in-memory with optional periodic persistence
    to disk. As observations accumulate, the router builds provider
    performance profiles and surfaces recommendations for downstream
    routing decisions.
    """

    def __init__(self, persist_path: str = ""):
        self._lock = threading.Lock()
        self._records: list[TelemetryRecord] = []
        self._persist_path = persist_path or os.path.join(
            os.path.expanduser("~"), ".shunya", "inference_router_telemetry.jsonl"
        )
        self._scores_cache: dict[str, ProviderScore] = {}
        self._scores_dirty = False

        # Ensure persistence directory exists
        persist_dir = os.path.dirname(self._persist_path)
        if persist_dir and not os.path.exists(persist_dir):
            try:
                os.makedirs(persist_dir, exist_ok=True)
            except OSError:
                pass  # Non-critical; we'll still work in-memory

        # Load existing telemetry on startup
        self._load_telemetry()

    # ── Public API ──────────────────────────────────────────────────────

    def record(self, record: TelemetryRecord) -> None:
        """Record a single inference telemetry observation.

        Thread-safe. Invalidates the score cache so the next
        recommendation recomputes from fresh data.
        """
        with self._lock:
            self._records.append(record)
            self._scores_dirty = True
            self._append_to_persist(record)
            logger.debug(
                "Recorded telemetry: provider=%s model=%s success=%s latency=%.0fms",
                record.provider, record.model, record.success, record.latency_ms,
            )

    def record_from_result(
        self,
        session_id: str,
        provider: str,
        model: str,
        request_type: str,
        result: Any,
        latency_ms: float,
    ) -> None:
        """Convenience: record telemetry from an InferenceResult object."""
        usage = getattr(result, "usage", {}) or {}
        record = TelemetryRecord(
            session_id=session_id,
            provider=provider,
            model=model,
            request_type=request_type,
            input_tokens=usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0),
            output_tokens=usage.get("output_tokens", 0) or usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            success=result.success if hasattr(result, "success") else True,
            error=getattr(result, "error", None),
            finish_reason=getattr(result, "finish_reason", "stop"),
        )
        self.record(record)

    def get_recommendation(
        self,
        context: dict | None = None,
        preferred_providers: list[str] | None = None,
    ) -> Recommendation:
        """Get the best provider recommendation based on observed telemetry.

        Args:
            context: Optional request context (request_type, complexity, etc.)
            preferred_providers: Optional list of preferred providers to restrict to.

        Returns:
            A Recommendation with the top-scoring provider+model.
        """
        scores = self._compute_scores()
        if not scores:
            # No data yet — return a neutral recommendation
            return Recommendation(
                provider="auto",
                model="",
                confidence=0.0,
                reason="No telemetry available yet — using default routing",
            )

        # Filter by preferred providers if specified
        if preferred_providers:
            candidates = [
                s for s in scores if s.provider in preferred_providers
            ]
        else:
            candidates = list(scores)

        if not candidates:
            return Recommendation(
                provider="auto",
                model="",
                confidence=0.0,
                reason="No providers match the preferred list",
            )

        # Sort by composite score (descending)
        candidates.sort(key=lambda s: s.score, reverse=True)
        best = candidates[0]

        # Build alternatives
        alternatives = [
            {"provider": s.provider, "model": s.model, "score": round(s.score, 3)}
            for s in candidates[1:4]
        ]

        return Recommendation(
            provider=best.provider,
            model=best.model,
            confidence=min(best.score / 100.0, 1.0),
            reason=f"Top performer: {best.provider}/{best.model} "
                   f"(success rate={1 - best.error_rate:.1%}, "
                   f"avg latency={best.avg_latency_ms:.0f}ms)",
            alternatives=alternatives,
        )

    def get_insights(
        self,
        time_range_hours: int = 24,
        provider_filter: str | None = None,
    ) -> dict:
        """Get aggregated insights from recent telemetry.

        Args:
            time_range_hours: How far back to look (default 24h).
            provider_filter: Optional provider name to filter by.

        Returns:
            Dict with summary stats, per-provider breakdowns, and trends.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        with self._lock:
            recent = [
                r for r in self._records
                if r.timestamp >= cutoff.isoformat()
            ]

        if provider_filter:
            recent = [r for r in recent if r.provider == provider_filter]

        if not recent:
            return {
                "time_range_hours": time_range_hours,
                "total_requests": 0,
                "providers": {},
                "summary": "No telemetry in this time range.",
            }

        # Per-provider aggregation
        provider_stats: dict[str, dict] = {}
        for r in recent:
            key = r.provider
            if key not in provider_stats:
                provider_stats[key] = {
                    "total": 0, "successful": 0, "errors": 0,
                    "total_latency": 0.0, "total_input_tokens": 0,
                    "total_output_tokens": 0, "latencies": [],
                }
            stats = provider_stats[key]
            stats["total"] += 1
            if r.success:
                stats["successful"] += 1
            else:
                stats["errors"] += 1
            stats["total_latency"] += r.latency_ms
            stats["total_input_tokens"] += r.input_tokens
            stats["total_output_tokens"] += r.output_tokens
            stats["latencies"].append(r.latency_ms)

        # Build per-provider summary
        providers = {}
        for name, stats in provider_stats.items():
            latencies = sorted(stats["latencies"])
            p50 = latencies[len(latencies) // 2] if latencies else 0
            p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
            providers[name] = {
                "total_requests": stats["total"],
                "successful_requests": stats["successful"],
                "error_rate": round(stats["errors"] / max(stats["total"], 1), 3),
                "avg_latency_ms": round(stats["total_latency"] / max(stats["total"], 1), 1),
                "p50_latency_ms": round(p50, 1),
                "p95_latency_ms": round(p95, 1),
                "avg_input_tokens": round(stats["total_input_tokens"] / max(stats["total"], 1)),
                "avg_output_tokens": round(stats["total_output_tokens"] / max(stats["total"], 1)),
            }

        total = len(recent)
        successful = sum(1 for r in recent if r.success)
        total_latency = sum(r.latency_ms for r in recent)

        return {
            "time_range_hours": time_range_hours,
            "total_requests": total,
            "successful_requests": successful,
            "error_rate": round(1 - (successful / max(total, 1)), 3),
            "avg_latency_ms": round(total_latency / max(total, 1), 1),
            "providers": providers,
            "summary": (
                f"{total} requests in last {time_range_hours}h, "
                f"{successful} successful ({successful / max(total, 1):.0%}), "
                f"avg latency {total_latency / max(total, 1):.0f}ms"
            ),
        }

    def get_records(
        self,
        limit: int = 100,
        offset: int = 0,
        provider_filter: str | None = None,
    ) -> list[dict]:
        """Get raw telemetry records (paginated)."""
        with self._lock:
            records = list(self._records)

        if provider_filter:
            records = [r for r in records if r.provider == provider_filter]

        records.reverse()  # newest first
        return [r.to_dict() for r in records[offset:offset + limit]]

    def get_record_count(self) -> int:
        """Return total number of telemetry records stored."""
        with self._lock:
            return len(self._records)

    def reset(self) -> None:
        """Clear all records and scores (for testing)."""
        with self._lock:
            self._records.clear()
            self._scores_cache.clear()
            self._scores_dirty = False

    # ── Internal ────────────────────────────────────────────────────────

    def _compute_scores(self) -> list[ProviderScore]:
        """Compute performance scores for each provider/model.

        Score formula (higher = better):
            score = (success_rate * 50) + (max(0, 1 - latency_ratio) * 30) + (throughput_ratio * 20)

        Where:
            - success_rate = successful / total
            - latency_ratio = avg_latency / max_latency (across all providers)
            - throughput_ratio = avg_output_tokens / max_output_tokens (across all providers)
        """
        with self._lock:
            if not self._scores_dirty and self._scores_cache:
                return list(self._scores_cache.values())

            if not self._records:
                return []

            # Group by provider+model
            groups: dict[str, list[TelemetryRecord]] = defaultdict(list)
            for r in self._records:
                groups[f"{r.provider}/{r.model}"].append(r)

            scores: list[ProviderScore] = []
            max_avg_latency = 0.0
            max_avg_output = 0

            # First pass: compute aggregates
            for key, recs in groups.items():
                provider, model = key.split("/", 1)
                total = len(recs)
                successful = sum(1 for r in recs if r.success)
                latencies = sorted(r.latency_ms for r in recs)
                avg_latency = sum(r.latency_ms for r in recs) / total
                avg_input = sum(r.input_tokens for r in recs) // total
                avg_output = sum(r.output_tokens for r in recs) // total
                p50 = latencies[len(latencies) // 2] if latencies else 0
                p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
                error_rate = 1 - (successful / total)

                scores.append(ProviderScore(
                    provider=provider,
                    model=model,
                    total_requests=total,
                    successful_requests=successful,
                    avg_latency_ms=avg_latency,
                    avg_input_tokens=avg_input,
                    avg_output_tokens=avg_output,
                    p50_latency_ms=p50,
                    p95_latency_ms=p95,
                    error_rate=error_rate,
                    score=0.0,  # computed below
                ))
                max_avg_latency = max(max_avg_latency, avg_latency)
                max_avg_output = max(max_avg_output, avg_output)

            # Second pass: compute composite scores
            for s in scores:
                success_rate = s.successful_requests / max(s.total_requests, 1)
                latency_ratio = s.avg_latency_ms / max(max_avg_latency, 1)
                throughput_ratio = s.avg_output_tokens / max(max_avg_output, 1)

                s.score = (
                    (success_rate * 50.0)
                    + (max(0.0, 1.0 - latency_ratio) * 30.0)
                    + (throughput_ratio * 20.0)
                )

            scores.sort(key=lambda s: s.score, reverse=True)
            self._scores_cache = {f"{s.provider}/{s.model}": s for s in scores}
            self._scores_dirty = False
            return scores

    def _load_telemetry(self) -> None:
        """Load persisted telemetry from disk on startup."""
        if not os.path.exists(self._persist_path):
            return
        try:
            with open(self._persist_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    self._records.append(TelemetryRecord(**data))
            logger.info(
                "Loaded %d telemetry records from %s",
                len(self._records), self._persist_path,
            )
        except Exception as e:
            logger.warning("Failed to load telemetry from %s: %s", self._persist_path, e)

    def _append_to_persist(self, record: TelemetryRecord) -> None:
        """Append a single record to the persistence file."""
        try:
            with open(self._persist_path, "a") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
        except OSError as e:
            logger.warning("Failed to persist telemetry: %s", e)