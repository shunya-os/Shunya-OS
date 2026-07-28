"""SHUNYA — Observer Engine canonical models (Phase J — ES-006).

Canonical observation data models: immutable representations of verified
observations, evidence validation results, deviation and anomaly reports,
learning signals, and supporting types.

Architectural authority: ES-006 — Observer Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ObservationType(Enum):
    """Types of observation (ES-006 §5)."""
    PASSIVE = "passive"
    ACTIVE = "active"
    CONTINUOUS = "continuous"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    COMPARATIVE = "comparative"
    PREDICTIVE = "predictive"
    HUMAN_ASSISTED = "human_assisted"


class ObservationSeverity(Enum):
    """Severity of an observation or anomaly (ES-006 §6)."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EvidenceValidationStatus(Enum):
    """Status of evidence validation per dimension (ES-006 §7)."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NOT_CHECKED = "not_checked"


class FailureMode(Enum):
    """Failure modes for observation processing (ES-006 §8)."""
    MISSING_EVIDENCE = "missing_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    TELEMETRY_FAILURE = "telemetry_failure"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    OBSERVATION_TIMEOUT = "observation_timeout"
    PARTIAL_OBSERVATION = "partial_observation"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


@dataclass
class Tolerance:
    """Acceptable variance thresholds per dimension (ES-006 §6)."""
    dimension: str
    warning_threshold: float = 0.1      # 10% variance → warning
    error_threshold: float = 0.25       # 25% variance → error
    critical_threshold: float = 0.5     # 50% variance → critical
    unit: str = "percent"

    def classify(self, delta_percentage: float) -> ObservationSeverity:
        """Classify a delta percentage against thresholds."""
        abs_delta = abs(delta_percentage)
        if abs_delta >= self.critical_threshold:
            return ObservationSeverity.CRITICAL
        if abs_delta >= self.error_threshold:
            return ObservationSeverity.ERROR
        if abs_delta >= self.warning_threshold:
            return ObservationSeverity.WARNING
        return ObservationSeverity.INFO


@dataclass
class ObservationVariance:
    """Quantified difference between expected and actual for one dimension."""
    dimension: str
    expected: Any = None
    actual: Any = None
    delta: float = 0.0
    delta_percentage: float = 0.0
    severity: str = ObservationSeverity.INFO.value
    explanation: str = ""


@dataclass
class ObservationState:
    """Measured state of an observed dimension (ES-006 §6)."""
    status: str = "unknown"           # success, partial, failed, pending, unknown
    dimensions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EvidenceValidationResult:
    """Result of validating evidence across 6 dimensions (ES-006 §7)."""
    completeness: EvidenceValidationStatus = EvidenceValidationStatus.NOT_CHECKED
    authenticity: EvidenceValidationStatus = EvidenceValidationStatus.NOT_CHECKED
    consistency: EvidenceValidationStatus = EvidenceValidationStatus.NOT_CHECKED
    correlation: EvidenceValidationStatus = EvidenceValidationStatus.NOT_CHECKED
    timestamp_integrity: EvidenceValidationStatus = EvidenceValidationStatus.NOT_CHECKED
    provenance: EvidenceValidationStatus = EvidenceValidationStatus.NOT_CHECKED
    quality_score: float = 0.0         # 0.0 to 1.0

    @property
    def passed(self) -> bool:
        return all(
            s == EvidenceValidationStatus.PASS
            for s in (self.completeness, self.authenticity, self.consistency,
                      self.correlation, self.timestamp_integrity, self.provenance)
        )

    @property
    def any_failed(self) -> bool:
        return any(
            s == EvidenceValidationStatus.FAIL
            for s in (self.completeness, self.authenticity, self.consistency,
                      self.correlation, self.timestamp_integrity, self.provenance)
        )


@dataclass
class DeviationReport:
    """Quantified deviation between expected and actual (ES-006 §3)."""
    deviation_id: str = ""
    dimension: str = ""
    expected_value: Any = None
    actual_value: Any = None
    delta: float = 0.0
    delta_percentage: float = 0.0
    severity: str = ObservationSeverity.INFO.value
    tolerance_used: Optional[Tolerance] = None

    def __post_init__(self) -> None:
        if not self.deviation_id:
            self.deviation_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deviation_id": self.deviation_id,
            "dimension": self.dimension,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "delta": self.delta,
            "delta_percentage": self.delta_percentage,
            "severity": self.severity,
        }


@dataclass
class AnomalyReport:
    """Report of an unexpected pattern or outlier (ES-006 §3)."""
    anomaly_id: str = ""
    pattern: str = ""
    description: str = ""
    severity: str = ObservationSeverity.WARNING.value
    dimension: str = ""
    observed_value: Any = None
    expected_pattern: str = ""

    def __post_init__(self) -> None:
        if not self.anomaly_id:
            self.anomaly_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "pattern": self.pattern,
            "description": self.description,
            "severity": self.severity,
            "dimension": self.dimension,
        }


@dataclass
class LearningSignal:
    """Structured learning signal for the Learning Engine (ES-006 §3)."""
    signal_id: str = ""
    observation_id: str = ""
    workflow_id: str = ""
    signal_type: str = ""        # "deviation" | "anomaly" | "success" | "failure"
    description: str = ""
    dimension: str = ""
    delta: float = 0.0
    delta_percentage: float = 0.0
    confidence: float = 0.5
    tenant_id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.signal_id:
            self.signal_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "observation_id": self.observation_id,
            "workflow_id": self.workflow_id,
            "signal_type": self.signal_type,
            "description": self.description,
            "dimension": self.dimension,
            "delta": self.delta,
            "delta_percentage": self.delta_percentage,
            "confidence": self.confidence,
            "tenant_id": self.tenant_id,
        }


@dataclass
class VerifiedObservation:
    """A validated, immutable record of what actually happened (ES-006 §3, §6)."""
    observation_id: str = ""
    workflow_id: str = ""
    plan_id: str = ""
    tenant_id: Optional[int] = None
    observation_type: str = ObservationType.PASSIVE.value
    observed_at: Optional[datetime] = None

    # Expected vs actual
    expected_state: Optional[ObservationState] = None
    actual_state: Optional[ObservationState] = None

    # Variances
    variances: List[ObservationVariance] = field(default_factory=list)

    # Quality
    evidence_quality: float = 0.0
    confidence: float = 0.0
    severity: str = ObservationSeverity.INFO.value

    # Evidence and anomalies
    evidence_validation: Optional[EvidenceValidationResult] = None
    anomalies: List[AnomalyReport] = field(default_factory=list)
    deviations: List[DeviationReport] = field(default_factory=list)

    # Learning signals
    learning_signals: List[LearningSignal] = field(default_factory=list)

    # Immutable metadata
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.observation_id:
            self.observation_id = str(uuid.uuid4())
        if self.observed_at is None:
            self.observed_at = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "workflow_id": self.workflow_id,
            "plan_id": self.plan_id,
            "tenant_id": self.tenant_id,
            "observation_type": self.observation_type,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "evidence_quality": self.evidence_quality,
            "confidence": self.confidence,
            "severity": self.severity,
            "variances": [
                {"dimension": v.dimension, "expected": v.expected, "actual": v.actual,
                 "delta": v.delta, "delta_percentage": v.delta_percentage,
                 "severity": v.severity, "explanation": v.explanation}
                for v in self.variances
            ],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "deviations": [d.to_dict() for d in self.deviations],
            "learning_signals": [s.to_dict() for s in self.learning_signals],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ObserverInput:
    """Input contract for observation (ES-006 §2)."""
    workflow_id: str = ""
    plan_id: str = ""
    tenant_id: Optional[int] = None

    # Execution outcome from Phase I Executor Engine
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    failures: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    workflow_state: str = ""

    # Expected outcomes (optional — from plan/reasoning)
    expected_tasks: Optional[List[Dict[str, Any]]] = None
    expected_metrics: Optional[Dict[str, Any]] = None

    # Observation metadata
    observation_type: str = ObservationType.PASSIVE.value

    def validate(self) -> List[str]:
        """Validate input and return list of error messages."""
        errors: List[str] = []
        if not self.workflow_id:
            errors.append("UNKNOWN_WORKFLOW: workflow_id is required")
        if self.tenant_id is None or self.tenant_id <= 0:
            errors.append("TENANT_MISMATCH: missing or invalid tenant_id")
        if not self.tasks and not self.failures:
            errors.append("EMPTY_OBSERVATION: no tasks or failures to observe")
        return errors


@dataclass
class ObserverOutput:
    """Output contract for observation (ES-006 §3)."""
    observation_id: str = ""
    observation: Optional[VerifiedObservation] = None
    anomaly_reports: List[AnomalyReport] = field(default_factory=list)
    deviation_reports: List[DeviationReport] = field(default_factory=list)
    learning_signals: List[LearningSignal] = field(default_factory=list)
    success: bool = True
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "observation": self.observation.to_dict() if self.observation else None,
            "anomaly_reports": [a.to_dict() for a in self.anomaly_reports],
            "deviation_reports": [d.to_dict() for d in self.deviation_reports],
            "learning_signals": [s.to_dict() for s in self.learning_signals],
            "success": self.success,
        }


@dataclass
class ObserverStats:
    """Observer engine statistics."""
    total_observations: int = 0
    with_anomalies: int = 0
    with_deviations: int = 0
    with_evidence_failures: int = 0
    avg_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_observations": self.total_observations,
            "with_anomalies": self.with_anomalies,
            "with_deviations": self.with_deviations,
            "with_evidence_failures": self.with_evidence_failures,
            "avg_confidence": round(self.avg_confidence, 2),
        }