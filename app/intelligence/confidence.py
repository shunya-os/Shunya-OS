"""
SHUNYA Explainable Intelligence — Confidence Model

Confidence is never decorative.
Confidence must be computed.

Confidence reflects:
  - Evidence completeness
  - Observation freshness
  - Source reliability
  - Relationship consistency
  - Conflict detection
  - Recency
  - Missing information

Unknowns reduce confidence.
Strong evidence increases confidence.
Hardcoded percentages are prohibited.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional


# ─── Default weights ───
# These are calibrated to produce confidence scores in a reasonable range.
# They can be overridden per context.

DEFAULT_WEIGHTS = {
    "evidence_completeness": 0.25,
    "observation_freshness": 0.20,
    "source_reliability": 0.20,
    "relationship_consistency": 0.15,
    "recency": 0.10,
    "missing_information_penalty": 0.10,
}


@dataclass
class ConfidenceInput:
    """Inputs to the confidence calculation.

    All values are 0.0 to 1.0 unless otherwise noted.
    None means the factor was not evaluated (reduces confidence).
    """

    evidence_completeness: Optional[float] = None
    """What fraction of expected evidence is available. 1.0 = all evidence present."""

    observation_freshness: Optional[float] = None
    """How fresh the observations are. 1.0 = just observed, decays over time."""

    source_reliability: Optional[float] = None
    """How reliable the source is. 1.0 = highly reliable source."""

    relationship_consistency: Optional[float] = None
    """How consistent the relationships are. 1.0 = all relationships consistent."""

    conflict_detected: bool = False
    """Whether conflicting evidence was detected. Conflicts reduce confidence."""

    recency_hours: Optional[float] = None
    """Hours since the last relevant observation. None = unknown."""

    missing_information_ratio: Optional[float] = None
    """Fraction of expected information that is missing. 0.0 = nothing missing."""

    def __post_init__(self):
        for field_name in [
            "evidence_completeness",
            "observation_freshness",
            "source_reliability",
            "relationship_consistency",
            "missing_information_ratio",
        ]:
            val = getattr(self, field_name)
            if val is not None and not 0.0 <= val <= 1.0:
                raise ValueError(
                    f"{field_name} must be between 0.0 and 1.0, got {val}"
                )


def compute_confidence(inputs: ConfidenceInput, weights: Optional[dict] = None) -> float:
    """Compute a confidence score from input factors.

    Returns a float between 0.0 and 1.0.
    Unknown factors reduce confidence proportionally.
    Conflicts apply a multiplicative penalty.
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    # ─── Known factors with weights ───
    known_factors: list[tuple[Optional[float], float]] = [
        (inputs.evidence_completeness, w["evidence_completeness"]),
        (inputs.observation_freshness, w["observation_freshness"]),
        (inputs.source_reliability, w["source_reliability"]),
        (inputs.relationship_consistency, w["relationship_consistency"]),
    ]

    # Recency: convert hours to a 0-1 score (decays exponentially)
    recency_score = None
    if inputs.recency_hours is not None:
        # Half-life of 72 hours (3 days)
        recency_score = 2.0 ** (-inputs.recency_hours / 72.0)
    known_factors.append((recency_score, w["recency"]))

    # Missing information penalty
    missing_penalty = 1.0
    if inputs.missing_information_ratio is not None:
        missing_penalty = 1.0 - (inputs.missing_information_ratio * w["missing_information_penalty"])

    # ─── Calculate weighted sum of known factors ───
    total_weight = 0.0
    weighted_sum = 0.0

    for value, weight in known_factors:
        if value is not None:
            weighted_sum += value * weight
            total_weight += weight
        # Unknown factors contribute nothing to numerator or denominator

    # If all factors are unknown, return 0.0
    if total_weight == 0.0:
        return 0.0

    # Normalize by total weight of known factors
    base_score = weighted_sum / total_weight

    # Apply missing information penalty
    base_score *= missing_penalty

    # Apply conflict penalty (multiplicative: -20% if conflict detected)
    if inputs.conflict_detected:
        base_score *= 0.8

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, base_score))


def confidence_label(score: float) -> str:
    """Convert a numeric confidence score to a human-readable label."""
    if score >= 0.9:
        return "Very high confidence"
    elif score >= 0.75:
        return "High confidence"
    elif score >= 0.5:
        return "Medium confidence"
    elif score >= 0.25:
        return "Low confidence"
    else:
        return "Very low confidence"


def confidence_breakdown(inputs: ConfidenceInput, weights: Optional[dict] = None) -> dict:
    """Return a detailed breakdown of the confidence calculation.

    Useful for the Founder Inspector to show why a particular
    confidence score was computed.
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)
    breakdown = {
        "factors": {},
        "total_score": compute_confidence(inputs, w),
        "conflict_penalty_applied": inputs.conflict_detected,
    }

    factor_map = {
        "evidence_completeness": "Evidence completeness",
        "observation_freshness": "Observation freshness",
        "source_reliability": "Source reliability",
        "relationship_consistency": "Relationship consistency",
        "recency_hours": "Recency",
        "missing_information_ratio": "Missing information",
    }

    for field, label in factor_map.items():
        val = getattr(inputs, field)
        if val is not None:
            breakdown["factors"][label] = {
                "value": val,
                "weight": w.get(field.replace("_hours", "").replace("_ratio", ""), "N/A"),
            }
        else:
            breakdown["factors"][label] = {
                "value": None,
                "note": "Not evaluated — reduces confidence",
            }

    return breakdown