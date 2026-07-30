"""Quota Manager — tracks RPM / TPM / RPD with graceful migration levels.

Quota levels
------------
- ``ok``        : under 75 % of any limit
- ``warn``      : at or above 75 % (graceful degradation starts)
- ``critical``  : at or above 90 % (aggressive back-off)
- ``exhausted`` : at or above 100 % (requests rejected)

The manager never raises on exhaustion — ``check_quota`` returns a
structured ``QuotaStatus`` so callers can choose their own degradation
strategy (queue, fallback, budget-aware prompt trimming, etc.).
"""

from __future__ import annotations

import enum
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ── Public types ────────────────────────────────────────────────────────────


class QuotaLevel(str, enum.Enum):
    OK = "ok"
    WARN = "warn"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


@dataclass
class QuotaStatus:
    """Returned by ``check_quota`` — a snapshot of quota health."""

    level: QuotaLevel
    model: str
    rpm_used: int = 0
    rpm_limit: int = 0
    tpm_used: int = 0
    tpm_limit: int = 0
    rpd_used: int = 0
    rpd_limit: int = 0
    message: str = ""

    @property
    def is_ok(self) -> bool:
        return self.level == QuotaLevel.OK

    @property
    def is_warn(self) -> bool:
        return self.level == QuotaLevel.WARN

    @property
    def is_critical(self) -> bool:
        return self.level == QuotaLevel.CRITICAL

    @property
    def is_exhausted(self) -> bool:
        return self.level == QuotaLevel.EXHAUSTED

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "model": self.model,
            "rpm_used": self.rpm_used,
            "rpm_limit": self.rpm_limit,
            "tpm_used": self.tpm_used,
            "tpm_limit": self.tpm_limit,
            "rpd_used": self.rpd_used,
            "rpd_limit": self.rpd_limit,
            "message": self.message,
        }


@dataclass
class UsageRecord:
    """A single usage event recorded by ``record_usage``."""

    model: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


# ── Quota Manager ──────────────────────────────────────────────────────────


class QuotaManager:
    """Thread-safe quota tracker with per-model rate limits.

    Default limits (configurable per model)::

        rpm=60, tpm=100_000, rpd=1_000_000
    """

    WARN_FRACTION = 0.75
    CRITICAL_FRACTION = 0.90
    EXHAUSTED_FRACTION = 1.00

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # model -> {model: ModelLimits}
        self._limits: dict[str, _ModelLimits] = {}
        # sliding window counts
        self._rpm_window: dict[str, list[float]] = defaultdict(list)  # timestamps
        self._tpm_window: dict[str, list[tuple[int, float]]] = defaultdict(list)
        self._rpd_count: dict[str, int] = defaultdict(int)
        self._rpd_reset_day: dict[str, int] = defaultdict(int)  # day-of-year

    # ── Configuration ───────────────────────────────────────────────────

    def set_limits(
        self,
        model: str,
        rpm: int = 60,
        tpm: int = 100_000,
        rpd: int = 1_000_000,
    ) -> None:
        """Set (or update) rate limits for a model."""
        with self._lock:
            self._limits[model] = _ModelLimits(rpm=rpm, tpm=tpm, rpd=rpd)
            logger.info(
                "Quota limits for %s: rpm=%d tpm=%d rpd=%d",
                model, rpm, tpm, rpd,
            )

    def get_limits(self, model: str) -> dict[str, int]:
        """Return the current limits for *model* as a dict."""
        with self._lock:
            limits = self._limits.get(model)
            if limits is None:
                return {"rpm": 60, "tpm": 100_000, "rpd": 1_000_000}
            return {"rpm": limits.rpm, "tpm": limits.tpm, "rpd": limits.rpd}

    # ── Recording ───────────────────────────────────────────────────────

    def record_usage(self, record: UsageRecord) -> None:
        """Record a usage event for quota tracking."""
        now = record.timestamp or time.time()
        day = time.gmtime(now).tm_yday

        with self._lock:
            model = record.model
            # RPM / TPM sliding windows
            self._rpm_window[model].append(now)
            self._tpm_window[model].append((record.tokens_input + record.tokens_output, now))
            # RPD counter
            if self._rpd_reset_day[model] != day:
                self._rpd_count[model] = 0
                self._rpd_reset_day[model] = day
            self._rpd_count[model] += record.tokens_input + record.tokens_output

            # Evict old entries from sliding windows (keep last 60s)
            cutoff = now - 60.0
            self._rpm_window[model] = [t for t in self._rpm_window[model] if t > cutoff]
            self._tpm_window[model] = [(t, ts) for t, ts in self._tpm_window[model] if ts > cutoff]

            logger.debug(
                "Recorded usage for %s: +%d tokens (rpm=%d, tpm=%d, rpd=%d)",
                model,
                record.tokens_input + record.tokens_output,
                len(self._rpm_window[model]),
                sum(t for t, _ in self._tpm_window[model]),
                self._rpd_count[model],
            )

    # ── Quota Check ─────────────────────────────────────────────────────

    def check_quota(self, model: str) -> QuotaStatus:
        """Check current quota health for *model*.

        Returns a ``QuotaStatus`` with the appropriate level.
        """
        with self._lock:
            limits = self._limits.get(model)
            if limits is None:
                limits = _ModelLimits(rpm=60, tpm=100_000, rpd=1_000_000)

            now = time.time()
            cutoff = now - 60.0

            # Prune stale window entries
            self._rpm_window[model] = [t for t in self._rpm_window[model] if t > cutoff]
            self._tpm_window[model] = [(t, ts) for t, ts in self._tpm_window[model] if ts > cutoff]

            rpm_used = len(self._rpm_window[model])
            tpm_used = sum(t for t, _ in self._tpm_window[model])
            rpd_used = self._rpd_count[model]

            ratios = [
                rpm_used / limits.rpm if limits.rpm > 0 else 0.0,
                tpm_used / limits.tpm if limits.tpm > 0 else 0.0,
                rpd_used / limits.rpd if limits.rpd > 0 else 0.0,
            ]
            max_ratio = max(ratios)

            if max_ratio >= self.EXHAUSTED_FRACTION:
                level = QuotaLevel.EXHAUSTED
                msg = (
                    f"Quota exhausted for {model}: "
                    f"rpm={rpm_used}/{limits.rpm}, "
                    f"tpm={tpm_used}/{limits.tpm}, "
                    f"rpd={rpd_used}/{limits.rpd}"
                )
            elif max_ratio >= self.CRITICAL_FRACTION:
                level = QuotaLevel.CRITICAL
                msg = (
                    f"Quota critical for {model}: "
                    f"rpm={rpm_used}/{limits.rpm}, "
                    f"tpm={tpm_used}/{limits.tpm}, "
                    f"rpd={rpd_used}/{limits.rpd}"
                )
            elif max_ratio >= self.WARN_FRACTION:
                level = QuotaLevel.WARN
                msg = (
                    f"Quota warning for {model}: "
                    f"rpm={rpm_used}/{limits.rpm}, "
                    f"tpm={tpm_used}/{limits.tpm}, "
                    f"rpd={rpd_used}/{limits.rpd}"
                )
            else:
                level = QuotaLevel.OK
                msg = f"Quota ok for {model}"

            logger.log(
                logging.WARNING if level in (QuotaLevel.WARN, QuotaLevel.CRITICAL, QuotaLevel.EXHAUSTED) else logging.DEBUG,
                "%s: rpm=%d/%d tpm=%d/%d rpd=%d/%d",
                level.value.upper(),
                rpm_used, limits.rpm,
                tpm_used, limits.tpm,
                rpd_used, limits.rpd,
            )

            return QuotaStatus(
                level=level,
                model=model,
                rpm_used=rpm_used,
                rpm_limit=limits.rpm,
                tpm_used=tpm_used,
                tpm_limit=limits.tpm,
                rpd_used=rpd_used,
                rpd_limit=limits.rpd,
                message=msg,
            )

    # ── Utility ─────────────────────────────────────────────────────────

    def reset(self, model: str | None = None) -> None:
        """Reset quota tracking for *model* (or all models if ``None``)."""
        with self._lock:
            if model is None:
                self._rpm_window.clear()
                self._tpm_window.clear()
                self._rpd_count.clear()
                self._rpd_reset_day.clear()
            else:
                self._rpm_window.pop(model, None)
                self._tpm_window.pop(model, None)
                self._rpd_count.pop(model, None)
                self._rpd_reset_day.pop(model, None)
            logger.info("Quota reset for %s", model or "ALL MODELS")


# ── Internal helpers ────────────────────────────────────────────────────────


@dataclass
class _ModelLimits:
    rpm: int = 60
    tpm: int = 100_000
    rpd: int = 1_000_000