"""Proactive Intelligence — signal-driven alerts and recommendations.

Phase 4 bridge: connects signal detection → SuggestionsEngine, adds proactive
alerts for overdue commitments, sales changes, financial anomalies, and
operational exceptions, and wires observations into the suggestion pipeline.

Every proactive signal carries confidence, source, and timestamp for
governance and auditability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .types import UniversalSuggestion, ContextFrame
from .suggestions import SuggestionsEngine

logger = logging.getLogger(__name__)


# ── Proactive Signal Types ─────────────────────────────────────────────────


@dataclass
class ProactiveSignal:
    """A proactive alert or recommendation with provenance metadata.

    Carries confidence, source, and timestamp so every signal is attributable
    and auditable (Phase 4.8).
    """
    key: str
    title: str
    description: str
    signal_type: str  # "alert" | "recommendation" | "reminder" | "insight"
    confidence: float = 0.0
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_suggestion(self) -> UniversalSuggestion:
        """Convert this signal into a UniversalSuggestion for the engine."""
        return UniversalSuggestion(
            key=self.key,
            title=self.title,
            description=self.description,
            suggestion_type=self.signal_type,
            confidence=self.confidence,
        )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "signal_type": self.signal_type,
            "confidence": round(self.confidence, 2),
            "source": self.source,
            "timestamp": self.timestamp,
            "evidence": self.evidence,
        }


# ── SignalBridge — connects app signals to SuggestionsEngine ──────────────


class SignalBridge:
    """Listens for SHUNYA signals and routes them to the SuggestionsEngine.

    Phase 4.1: Connects app/signals/ (Signal model, emit_signal) to the
    runtime's SuggestionsEngine so detected signals produce proactive
    recommendations.
    """

    def __init__(self, suggestions_engine: SuggestionsEngine | None = None):
        self._engine = suggestions_engine or SuggestionsEngine()
        self._listeners: dict[str, list[Callable]] = {}
        self._signal_history: list[ProactiveSignal] = []

    def set_engine(self, engine: SuggestionsEngine) -> None:
        self._engine = engine

    def get_engine(self) -> SuggestionsEngine:
        return self._engine

    # ── Listener API ──────────────────────────────────────────────────────

    def on(self, signal_type: str, handler: Callable) -> None:
        """Register a handler for a signal type."""
        self._listeners.setdefault(signal_type, []).append(handler)

    def off(self, signal_type: str, handler: Callable) -> None:
        """Remove a handler for a signal type."""
        handlers = self._listeners.get(signal_type, [])
        if handler in handlers:
            handlers.remove(handler)

    # ── Core routing (Phase 4.1) ──────────────────────────────────────────

    def route_signal(self, sig_type: str, payload: dict | None = None,
                     identity_id: str = "", tenant_id: str = "") -> ProactiveSignal | None:
        """Route an incoming SHUNYA signal and produce a ProactiveSignal.

        Called by the signal system when a new Signal is emitted. The bridge
        checks for registered listeners and the SuggestionsEngine, then returns
        a ProactiveSignal if one was produced.
        """
        payload = payload or {}

        # 1. Call registered listeners for this signal type
        results: list[ProactiveSignal] = []
        for handler in self._listeners.get(sig_type, []):
            try:
                result = handler(payload, identity_id=identity_id, tenant_id=tenant_id)
                if result:
                    results.append(result)
            except Exception as exc:
                logger.warning("Signal listener failed for %s: %s", sig_type, exc)

        # 2. Generate context-aware suggestion via the engine
        context = ContextFrame(
            identity_id=identity_id,
            tenant_id=tenant_id,
            current_task=payload.get("reason", ""),
            active_module=payload.get("module", ""),
            active_object_type=payload.get("object_type", ""),
            active_object_id=str(payload.get("object_id", "")),
        )
        suggestions = self._engine.suggest(context)
        for s in suggestions:
            results.append(ProactiveSignal(
                key=s.key,
                title=s.title,
                description=s.description,
                signal_type="recommendation",
                confidence=s.confidence,
                source="suggestions_engine",
                metadata={"context": context.to_dict()},
            ))

        # 3. Record and return the best signal
        signal = max(results, key=lambda x: x.confidence) if results else None
        if signal:
            self._signal_history.append(signal)
            self._signal_history = self._signal_history[-100:]  # bounded
        return signal

    def get_history(self, limit: int = 20) -> list[dict]:
        """Recent proactive signals for display."""
        return [s.to_dict() for s in self._signal_history[-limit:]]

    def clear_history(self) -> None:
        self._signal_history.clear()


# ── Domain-specific detectors (Phases 4.2–4.6) ────────────────────────────


def detect_overdue_commitments(identity_id: str = "",
                                tenant_id: str = "") -> list[ProactiveSignal]:
    """Query Outcome/Execution records for overdue items (Phase 4.2).

    Scans the sh_outcomes table for outcomes with a pending stage and an
    expected_completion_seconds that has elapsed — these are overdue
    commitments that should be surfaced as proactive reminders.
    """
    signals: list[ProactiveSignal] = []
    try:
        from app import db
        from app.execution.models import Outcome
        from sqlalchemy import text

        now = datetime.now(timezone.utc)

        # Query outcomes that are still pending with a deadline that has passed
        # The expected_completion_seconds is stored in state JSON.
        query = Outcome.query
        if identity_id:
            query = query.filter(Outcome.identity_id == identity_id)
        outcomes = query.order_by(Outcome.created_at.desc()).limit(50).all()

        for outcome in outcomes:
            state = outcome.state or {}
            stage = state.get("stage", "pending")
            if stage not in ("pending", "running", "active"):
                continue

            expected_sec = state.get("expected_completion_seconds", 0)
            if expected_sec <= 0:
                continue

            deadline_ts = outcome.created_at.replace(tzinfo=timezone.utc) if outcome.created_at else now
            deadline_ts = deadline_ts.timestamp() + expected_sec
            if now.timestamp() > deadline_ts:
                overdue_minutes = int((now.timestamp() - deadline_ts) / 60)
                signals.append(ProactiveSignal(
                    key=f"overdue_{outcome.outcome_id}",
                    title=f"Overdue: {outcome.intention[:60]}",
                    description=(
                        f"Commitment \"{outcome.intention[:120]}\" is {overdue_minutes} "
                        f"minutes overdue (stage: {stage}). Consider reviewing or escalating."
                    ),
                    signal_type="reminder",
                    confidence=min(0.5 + (overdue_minutes / 480), 0.9),  # ramps to 0.9 over 8h
                    source="proactive/overdue_commitments",
                    evidence=[{
                        "outcome_id": outcome.outcome_id,
                        "stage": stage,
                        "overdue_minutes": overdue_minutes,
                        "created_at": outcome.created_at.isoformat() if outcome.created_at else "",
                    }],
                ))
    except Exception as exc:
        logger.warning("Overdue commitment detection failed: %s", exc)

    return signals


def detect_unusual_sales_changes(identity_id: str = "",
                                  tenant_id: str = "") -> list[ProactiveSignal]:
    """Detect unusual sales changes as proactive alerts (Phase 4.3).

    Compares recent lead/opportunity counts against historical averages to
    flag spikes or drops in sales activity.
    """
    signals: list[ProactiveSignal] = []
    try:
        from app import db
        from sqlalchemy import func, text
        from datetime import timedelta

        # Try to query Lead table for recent vs historical counts
        try:
            from app.models import Lead
            now = datetime.now(timezone.utc)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)

            recent_count = db.session.query(func.count(Lead.id)).filter(
                Lead.created_at >= seven_days_ago
            ).scalar() or 0

            historical_count = db.session.query(func.count(Lead.id)).filter(
                Lead.created_at >= thirty_days_ago,
                Lead.created_at < seven_days_ago,
            ).scalar() or 0

            if historical_count > 0 and recent_count > 0:
                change_pct = ((recent_count - historical_count) / historical_count) * 100
                if abs(change_pct) > 30:  # significant change threshold
                    direction = "increase" if change_pct > 0 else "drop"
                    signals.append(ProactiveSignal(
                        key=f"sales_change_{now.timestamp():.0f}",
                        title=f"Unusual sales activity: {abs(change_pct):.0f}% {direction}",
                        description=(
                            f"Lead volume changed by {abs(change_pct):.0f}% over the last 7 days "
                            f"({recent_count} recent vs {historical_count} historical). "
                            f"This may warrant attention."
                        ),
                        signal_type="alert",
                        confidence=min(abs(change_pct) / 200, 0.85),
                        source="proactive/sales_changes",
                        evidence=[{
                            "recent_7d_count": recent_count,
                            "historical_21d_count": historical_count,
                            "change_pct": round(change_pct, 1),
                        }],
                    ))
        except Exception:
            logger.debug("Lead table unavailable for sales change detection")

    except Exception as exc:
        logger.warning("Sales change detection failed: %s", exc)

    return signals


def detect_financial_anomalies(identity_id: str = "",
                                tenant_id: str = "") -> list[ProactiveSignal]:
    """Detect financial anomalies as proactive alerts (Phase 4.4).

    Scans recent journal entries for unusual patterns: high-value entries,
    unposted entries aging, or reversal chains.
    """
    signals: list[ProactiveSignal] = []
    try:
        from app import db
        from sqlalchemy import func, text
        from datetime import timedelta

        try:
            from app.finance.models import JournalEntry

            now = datetime.now(timezone.utc)
            three_days_ago = now - timedelta(days=3)

            # Unposted entries aging
            unposted = db.session.query(func.count(JournalEntry.id)).filter(
                JournalEntry.status == "draft",
                JournalEntry.created_at < three_days_ago,
            ).scalar() or 0

            if unposted > 5:
                signals.append(ProactiveSignal(
                    key=f"unposted_entries_{now.timestamp():.0f}",
                    title=f"{unposted} unposted journal entries aging",
                    description=(
                        f"There are {unposted} draft journal entries that have not been "
                        f"posted for over 3 days. Review and post to keep accounts current."
                    ),
                    signal_type="alert",
                    confidence=min(0.5 + (unposted * 0.02), 0.85),
                    source="proactive/financial_anomalies",
                    evidence=[{"unposted_count": unposted, "aging_days": 3}],
                ))

            # High-value recent entries (potential anomalies)
            recent = db.session.query(JournalEntry).filter(
                JournalEntry.created_at >= three_days_ago,
            ).all()

            high_value_count = 0
            for entry in recent:
                try:
                    # Check associated journal lines for high values
                    lines_sql = text(
                        "SELECT COUNT(*) FROM fin_journal_lines "
                        "WHERE journal_entry_id = :eid AND ABS(amount) > 100000"
                    )
                    result = db.session.execute(lines_sql, {"eid": entry.id}).scalar()
                    if result and result > 0:
                        high_value_count += 1
                except Exception:
                    pass

            if high_value_count > 0:
                signals.append(ProactiveSignal(
                    key=f"high_value_entries_{now.timestamp():.0f}",
                    title=f"{high_value_count} high-value journal entries detected",
                    description=(
                        f"{high_value_count} recent journal entries contain line items "
                        f"exceeding 100,000. Verify these entries for accuracy."
                    ),
                    signal_type="alert",
                    confidence=0.7,
                    source="proactive/financial_anomalies",
                    evidence=[{"high_value_entry_count": high_value_count}],
                ))
        except Exception:
            logger.debug("Finance models unavailable for anomaly detection")

    except Exception as exc:
        logger.warning("Financial anomaly detection failed: %s", exc)

    return signals


def detect_operational_exceptions(identity_id: str = "",
                                   tenant_id: str = "") -> list[ProactiveSignal]:
    """Detect operational exceptions as proactive alerts (Phase 4.5).

    Examines execution logs for error patterns, stalled workflows, and
    repeated failures.
    """
    signals: list[ProactiveSignal] = []
    try:
        from app import db
        from sqlalchemy import func, text
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)

        # Check execution logs for errors in the last 24h
        try:
            from app.execution_engine.models import ExecutionLog
            error_count = db.session.query(func.count(ExecutionLog.id)).filter(
                ExecutionLog.created_at >= day_ago,
                ExecutionLog.action_type.ilike("%error%"),
            ).scalar() or 0

            if error_count > 3:
                signals.append(ProactiveSignal(
                    key=f"execution_errors_{now.timestamp():.0f}",
                    title=f"{error_count} execution errors in the last 24 hours",
                    description=(
                        f"Detected {error_count} execution errors in the past 24h. "
                        f"This exceeds the normal threshold and may indicate a systemic issue."
                    ),
                    signal_type="alert",
                    confidence=min(0.5 + (error_count * 0.05), 0.9),
                    source="proactive/operational_exceptions",
                    evidence=[{"error_count_24h": error_count}],
                ))
        except Exception:
            logger.debug("ExecutionLog model unavailable")

        # Check for outcomes in error state
        try:
            from app.execution.models import Outcome
            stalled = Outcome.query.filter(
                Outcome.state["stage"].astext == "error",
            ).count() if hasattr(Outcome.state, "astext") else 0

            if stalled > 2:
                signals.append(ProactiveSignal(
                    key=f"stalled_outcomes_{now.timestamp():.0f}",
                    title=f"{stalled} outcomes in error state",
                    description=(
                        f"There are {stalled} execution outcomes currently in an error state. "
                        f"These may need manual intervention or recovery."
                    ),
                    signal_type="alert",
                    confidence=0.75,
                    source="proactive/operational_exceptions",
                    evidence=[{"stalled_count": stalled}],
                ))
        except Exception:
            logger.debug("Outcome model unavailable for stall detection")

    except Exception as exc:
        logger.warning("Operational exception detection failed: %s", exc)

    return signals


def wire_observations_into_pipeline(identity_id: str = "",
                                     tenant_id: str = "") -> list[ProactiveSignal]:
    """Wire observations system into the suggestion pipeline (Phase 4.6).

    Reads active observations from the app.intelligence.observation module
    and converts high-confidence observations into proactive recommendations.
    """
    signals: list[ProactiveSignal] = []
    try:
        from app.intelligence.observation import get_store

        store = get_store()
        active = store.get_active() if hasattr(store, "get_active") else []

        for obs in active:
            if obs.confidence >= 0.7:
                signals.append(ProactiveSignal(
                    key=f"observation_{obs.observation_id}",
                    title=obs.label,
                    description=obs.description,
                    signal_type="insight",
                    confidence=obs.confidence,
                    source="observations_system",
                    evidence=[{
                        "observation_id": obs.observation_id,
                        "object_id": obs.object_id,
                        "event_id": obs.event_id,
                    }],
                    metadata=obs.metadata,
                ))
    except Exception as exc:
        logger.warning("Observations pipeline wiring failed: %s", exc)

    return signals


# ── Evidence-based recommendations (Phase 4.7) ────────────────────────────


def generate_evidence_based_recommendations(
    identity_id: str = "",
    tenant_id: str = "",
) -> list[ProactiveSignal]:
    """Generate evidence-backed proactive recommendations.

    Combines multiple signal sources (overdue commitments, sales changes,
    financial anomalies, operational exceptions, observations) and scores
    them by confidence to produce ranked recommendations with attached evidence.
    """
    signals: list[ProactiveSignal] = []

    # Gather from all detectors
    sources = [
        ("overdue_commitments", detect_overdue_commitments),
        ("sales_changes", detect_unusual_sales_changes),
        ("financial_anomalies", detect_financial_anomalies),
        ("operational_exceptions", detect_operational_exceptions),
        ("observations", wire_observations_into_pipeline),
    ]

    for source_name, detector in sources:
        try:
            source_signals = detector(identity_id=identity_id, tenant_id=tenant_id)
            signals.extend(source_signals)
        except Exception as exc:
            logger.warning("Evidence source %s failed: %s", source_name, exc)

    # Deduplicate by key
    seen = set()
    deduped = []
    for s in signals:
        if s.key not in seen:
            seen.add(s.key)
            deduped.append(s)

    # Sort by confidence descending
    deduped.sort(key=lambda x: (-x.confidence, x.timestamp), reverse=False)

    return deduped


# ── Bridge integration helper ─────────────────────────────────────────────


def create_proactive_bridge(
    suggestions_engine: SuggestionsEngine | None = None,
) -> SignalBridge:
    """Factory: create a fully wired SignalBridge.

    Wires all domain detectors as listeners so the bridge automatically
    produces proactive signals when route_signal is called.
    """
    bridge = SignalBridge(suggestions_engine=suggestions_engine)

    def _all_detectors_handler(payload: dict, identity_id: str = "",
                                tenant_id: str = "") -> list[ProactiveSignal]:
        return generate_evidence_based_recommendations(
            identity_id=identity_id, tenant_id=tenant_id,
        )

    # Wire a catch-all listener that runs all detectors
    bridge.on("*", _all_detectors_handler)

    return bridge


# ── Singleton support ─────────────────────────────────────────────────────

_PROACTIVE_BRIDGE: SignalBridge | None = None


def get_proactive_bridge() -> SignalBridge:
    global _PROACTIVE_BRIDGE
    if _PROACTIVE_BRIDGE is None:
        _PROACTIVE_BRIDGE = create_proactive_bridge()
    return _PROACTIVE_BRIDGE


def reset_proactive_bridge() -> None:
    global _PROACTIVE_BRIDGE
    _PROACTIVE_BRIDGE = None


def start_proactive_engine() -> None:
    """Start the proactive intelligence engine. Called from app factory (G3 Phase 4).

    Initializes the SignalBridge singleton and attaches all detectors.
    The bridge starts listening for signals and generating proactive
    recommendations.
    """
    bridge = get_proactive_bridge()
    logger.info("Proactive intelligence engine started with %d detector(s)",
                len(bridge._handlers) if hasattr(bridge, '_handlers') else 0)