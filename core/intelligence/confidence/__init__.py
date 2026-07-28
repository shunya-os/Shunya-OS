"""SHUNYA — Confidence Engine

Computes, combines, and tracks confidence scores across all engine outputs.
All confidence computation is deterministic and formula-based. Never escalates
to AI.

Capabilities:
    - Weighted average confidence computation
    - Bayesian-like confidence combination
    - Confidence history tracking
    - Score level classification (very_low, low, medium, high, very_high)

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §12 (Confidence Engine)
"""

from __future__ import annotations

from core.intelligence.confidence.engine import (
    ConfidenceEngine,
    ConfidenceFactor,
    ConfidenceScore,
)

__all__ = [
    "ConfidenceEngine",
    "ConfidenceFactor",
    "ConfidenceScore",
]