"""
SHUNYA — Canonical Awareness Service.

Gate 3.1: The authoritative pipeline for governing awareness.

Evaluates events, produces signals, filters by relevance, deduplicates,
suppresses storms, coalesces related events, and produces a calm
awareness state.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from core.awareness import (
    AwarenessSignal,
    AwarenessState,
    SignalPriority,
    SignalStatus,
    SignalType,
)

logger = logging.getLogger(__name__)


class AwarenessService:
    """Canonical awareness service — the single authoritative pipeline
    for turning real events into governed user-facing awareness.

    Pipeline:
        EVENT → SIGNAL → RELEVANCE → DEDUP → SUPPRESSION → COALESCING → ATTENTION
    """

    def __init__(self):
        self._signals: dict[str, AwarenessSignal] = {}      # signal_id → signal
        self._dedup_cache: dict[str, float] = {}            # dedup_key → timestamp
        self._suppression_counters: dict[str, int] = {}     # dedup_key → count
        self._recent_events: list[dict] = []

    # ── Main entry point ──────────────────────────────────────────────

    def process_event(self, event_type: str, event_data: dict,
                      tenant_id: int = 0) -> AwarenessSignal | None:
        """Process a canonical event and produce an awareness signal
        if relevant."""
        # 1. Evaluate relevance
        signal = self._evaluate_event(event_type, event_data, tenant_id)
        if signal is None:
            return None

        # 2. Deduplication
        if self._is_duplicate(signal):
            self._handle_duplicate(signal)
            return None

        # 3. Storm suppression
        if self._is_storm(signal):
            self._suppress_storm(signal)
            return None

        # 4. Store and return
        self._signals[signal.signal_id] = signal
        self._dedup_cache[signal.dedup_key] = time.time()
        self._recent_events.append({
            "signal_id": signal.signal_id,
            "type": signal.signal_type.value,
            "title": signal.title,
            "timestamp": signal.created_at,
        })
        if len(self._recent_events) > 100:
            self._recent_events = self._recent_events[-100:]

        return signal

    def get_state(self, tenant_id: int = 0) -> AwarenessState:
        """Get the current awareness state."""
        active = [s for s in self._signals.values()
                  if s.status == SignalStatus.ACTIVE
                  and (s.tenant_id == tenant_id or tenant_id == 0)]
        state = AwarenessState(
            signals=active,
            total_count=len(self._signals),
            active_count=len(active),
            critical_count=sum(1 for s in active if s.priority == SignalPriority.CRITICAL),
            high_count=sum(1 for s in active if s.priority == SignalPriority.HIGH),
            normal_count=sum(1 for s in active if s.priority == SignalPriority.NORMAL),
            calm=len(active) == 0,
        )
        return state

    def get_signals(self, tenant_id: int = 0,
                    status: SignalStatus | None = None,
                    limit: int = 20) -> list[AwarenessSignal]:
        """Get signals, optionally filtered by status."""
        result = []
        for s in self._signals.values():
            if s.tenant_id != tenant_id and tenant_id != 0:
                continue
            if status and s.status != status:
                continue
            result.append(s)
        return sorted(result, key=lambda x: x.created_at, reverse=True)[:limit]

    # ── Signal lifecycle ──────────────────────────────────────────────

    def acknowledge(self, signal_id: str) -> bool:
        if signal_id not in self._signals:
            return False
        self._signals[signal_id].status = SignalStatus.ACKNOWLEDGED
        self._signals[signal_id].acknowledged_at = datetime.now(timezone.utc).isoformat()
        return True

    def dismiss(self, signal_id: str) -> bool:
        if signal_id not in self._signals:
            return False
        self._signals[signal_id].status = SignalStatus.DISMISSED
        return True

    def snooze(self, signal_id: str, minutes: int = 30) -> bool:
        if signal_id not in self._signals:
            return False
        snooze_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self._signals[signal_id].status = SignalStatus.SNOOZED
        self._signals[signal_id].snoozed_until = snooze_until.isoformat()
        return True

    def resolve(self, signal_id: str) -> bool:
        if signal_id not in self._signals:
            return False
        self._signals[signal_id].status = SignalStatus.RESOLVED
        return True

    # ── Event evaluation ──────────────────────────────────────────────

    def _evaluate_event(self, event_type: str, event_data: dict,
                        tenant_id: int) -> AwarenessSignal | None:
        """Evaluate a canonical event and produce a signal if relevant."""
        signal_type = self._classify_event(event_type)
        if signal_type is None:
            return None

        title = self._extract_title(event_type, event_data)
        description = event_data.get("description", event_data.get("payload", {}).get("message", ""))
        object_id = event_data.get("object_id", event_data.get("object", {}).get("id", ""))
        object_type = event_data.get("object_type", event_data.get("object", {}).get("type", ""))
        priority = self._compute_priority(event_type, event_data)

        # Build evidence
        evidence = [{
            "source": event_type,
            "event_id": event_data.get("event_id", ""),
            "timestamp": event_data.get("timestamp", ""),
            "detail": description[:200] if description else title,
        }]

        reason = self._generate_reason(signal_type, title, priority)

        return AwarenessSignal(
            signal_type=signal_type,
            title=title,
            description=description[:300],
            reason=reason,
            source_event_id=event_data.get("event_id", ""),
            source_type="canonical_event",
            evidence=evidence,
            affected_object_id=object_id,
            affected_object_type=object_type,
            tenant_id=tenant_id,
            priority=priority,
            relevance_score=self._compute_relevance(signal_type, priority),
            knowledge_status="fact" if event_type.startswith("object_") else "inference",
            suggested_action=self._suggest_action(signal_type, event_type),
        )

    @staticmethod
    def _classify_event(event_type: str) -> SignalType | None:
        """Classify a canonical event type into a signal type."""
        if "object_created" in event_type or "ingestion:" in event_type:
            return SignalType.CHANGE
        if "object_updated" in event_type:
            return SignalType.ATTENTION
        if "execution_started" in event_type:
            return SignalType.ATTENTION
        if "execution_completed" in event_type or "success" in event_type:
            return SignalType.INFORMATION
        if "execution_failed" in event_type or "error" in event_type:
            return SignalType.RISK
        if "recovery" in event_type:
            return SignalType.INFORMATION
        if "commitment" in event_type or "due" in event_type:
            return SignalType.COMMITMENT
        if "insight" in event_type:
            return SignalType.OPPORTUNITY
        if "observation" in event_type:
            return SignalType.PATTERN
        if "external" in event_type or "research" in event_type:
            return SignalType.EXTERNAL
        return None

    @staticmethod
    def _extract_title(event_type: str, data: dict) -> str:
        """Extract a human-readable title from an event."""
        payload = data.get("payload", {})
        return (payload.get("message", "")
                or payload.get("title", "")
                or data.get("title", "")
                or data.get("event_type", event_type))

    @staticmethod
    def _compute_priority(event_type: str, data: dict) -> SignalPriority:
        """Compute signal priority from event type and data."""
        payload = data.get("payload", {})
        if "failed" in event_type or "error" in event_type:
            return SignalPriority.HIGH if payload.get("attempts", 0) > 1 else SignalPriority.NORMAL
        if "critical" in str(data.get("importance", "")).lower():
            return SignalPriority.CRITICAL
        if "high" in str(data.get("importance", "")).lower():
            return SignalPriority.HIGH
        if "commitment" in event_type or "due" in event_type:
            return SignalPriority.HIGH
        if "opportunity" in event_type or "insight" in event_type:
            return SignalPriority.NORMAL
        return SignalPriority.LOW

    @staticmethod
    def _compute_relevance(signal_type: SignalType, priority: SignalPriority) -> float:
        """Compute relevance score [0, 1]."""
        scores = {
            SignalPriority.CRITICAL: 1.0,
            SignalPriority.HIGH: 0.8,
            SignalPriority.NORMAL: 0.5,
            SignalPriority.LOW: 0.2,
        }
        base = scores.get(priority, 0.3)
        # Boost certain types
        if signal_type in (SignalType.RISK, SignalType.COMMITMENT, SignalType.OVERDUE):
            base = min(1.0, base + 0.1)
        return base

    @staticmethod
    def _generate_reason(signal_type: SignalType, title: str,
                         priority: SignalPriority) -> str:
        reasons = {
            SignalType.CHANGE: f"Something changed: {title[:100]}",
            SignalType.ATTENTION: f"This may need your attention: {title[:100]}",
            SignalType.RISK: f"Risk detected: {title[:100]}",
            SignalType.COMMITMENT: f"A commitment is approaching: {title[:100]}",
            SignalType.OPPORTUNITY: f"Opportunity detected: {title[:100]}",
            SignalType.INFORMATION: f"New information: {title[:100]}",
            SignalType.PATTERN: f"Pattern detected: {title[:100]}",
            SignalType.CONFLICT: f"Conflicting information: {title[:100]}",
            SignalType.OVERDUE: f"Overdue: {title[:100]}",
            SignalType.BLOCKED: f"Blocked: {title[:100]}",
            SignalType.EXTERNAL: f"External development: {title[:100]}",
        }
        return reasons.get(signal_type, f"Signal: {title[:100]}")

    @staticmethod
    def _suggest_action(signal_type: SignalType, event_type: str) -> str:
        actions = {
            SignalType.CHANGE: "Review changes",
            SignalType.ATTENTION: "View details",
            SignalType.RISK: "Assess risk",
            SignalType.COMMITMENT: "Review commitment",
            SignalType.OPPORTUNITY: "Explore opportunity",
            SignalType.INFORMATION: "View information",
            SignalType.PATTERN: "Investigate pattern",
            SignalType.CONFLICT: "Resolve conflict",
            SignalType.OVERDUE: "Take action",
            SignalType.BLOCKED: "Unblock",
            SignalType.EXTERNAL: "Review external development",
        }
        return actions.get(signal_type, "View details")

    # ── Storm prevention ──────────────────────────────────────────────

    def _is_duplicate(self, signal: AwarenessSignal) -> bool:
        return signal.dedup_key in self._dedup_cache

    def _handle_duplicate(self, signal: AwarenessSignal) -> None:
        key = signal.dedup_key
        self._suppression_counters[key] = self._suppression_counters.get(key, 0) + 1
        count = self._suppression_counters[key]
        if count > 3:
            logger.info("Storm suppressed: %s (count=%d)", key, count)

    def _is_storm(self, signal: AwarenessSignal) -> bool:
        key = signal.dedup_key
        if key not in self._dedup_cache:
            return False
        elapsed = time.time() - self._dedup_cache[key]
        # More than 5 duplicate events in 30 seconds = storm
        count = self._suppression_counters.get(key, 0)
        return count >= 5 and elapsed < 30.0

    def _suppress_storm(self, signal: AwarenessSignal) -> None:
        logger.info("Storm suppressed for: %s", signal.dedup_key)

    # ── Cleanup ───────────────────────────────────────────────────────

    def cleanup_expired(self, max_age_seconds: int = 86400) -> int:
        """Remove expired signals and old dedup cache entries."""
        now = time.time()
        expired = 0
        # Expire old dedup cache entries
        for key, ts in list(self._dedup_cache.items()):
            if now - ts > max_age_seconds:
                del self._dedup_cache[key]
                expired += 1
        # Expire old signals
        for sid, signal in list(self._signals.items()):
            if signal.expires_at:
                try:
                    exp = datetime.fromisoformat(signal.expires_at.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) > exp:
                        signal.status = SignalStatus.EXPIRED
                        expired += 1
                except (ValueError, TypeError):
                    pass
        return expired

    def clear(self) -> None:
        self._signals.clear()
        self._dedup_cache.clear()
        self._suppression_counters.clear()
        self._recent_events.clear()


# ── Module-level singleton ──────────────────────────────────────────

_service: Optional[AwarenessService] = None


def get_awareness_service() -> AwarenessService:
    global _service
    if _service is None:
        _service = AwarenessService()
    return _service


def reset_awareness_service() -> None:
    global _service
    _service = None


__all__ = [
    "AwarenessService",
    "get_awareness_service",
    "reset_awareness_service",
]