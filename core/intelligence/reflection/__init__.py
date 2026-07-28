"""
SHUNYA — Reflection Engine

Public API for the Reflection Engine. Evaluates outcomes of decisions and
actions: compares actual vs expected, detects anomalies, computes success
scores, and generates improvement signals for the Learning Engine.

Capabilities:
    - Outcome vs expected comparison
    - Anomaly detection (threshold-based)
    - Success score computation (weighted dimensions)
    - Improvement signal generation and categorization
    - Reflection record management

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §10 (Reflection Engine)
"""

from __future__ import annotations

from core.intelligence.reflection.engine import ReflectionEngine
from core.intelligence.reflection.models import (
    DEFAULT_ANOMALY_THRESHOLDS,
    DEFAULT_REFLECTION_WEIGHTS,
    Anomaly,
    AnomalySeverity,
    ImprovementSignal,
    ImprovementSignalCategory,
    OutcomeComparison,
    ReflectionRecord,
    SuccessScoreComponents,
)

__all__ = [
    "DEFAULT_ANOMALY_THRESHOLDS",
    "DEFAULT_REFLECTION_WEIGHTS",
    "Anomaly",
    "AnomalySeverity",
    "ImprovementSignal",
    "ImprovementSignalCategory",
    "OutcomeComparison",
    "ReflectionEngine",
    "ReflectionRecord",
    "SuccessScoreComponents",
]