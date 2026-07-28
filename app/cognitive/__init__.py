"""SHUNYA — Cognitive Validation & Traceability (Milestone VA)

Validates SHUNYA's complete cognitive pipeline. Guarantees every
recommendation can be reconstructed, replayed, audited, and trusted.

No new business capabilities. No new intelligence domains.
Validates the architecture already built.

Architecture:
  CognitiveTrace       → Complete reasoning trace from event to recommendation
  ReasoningReplay      → Deterministic replay from saved snapshots
  ConsistencyValidator → Cross-module reference verification
  ContradictionDetector → Detects conflicts across reasoning stages
  ConfidencePropagator → Tracks confidence through every stage
  ReasoningProvenance  → Fingerprints, versions, immutable audit
  AuditAPI             → Read-only APIs for replay and inspection
"""

from app.cognitive.models import (
    ReasoningNode, ReasoningGraph, TraceConfig,
    ReplayInput, ReplayResult, ReplayDiagnostic,
    ConsistencyCheck, ConsistencyResult,
    Contradiction, ContradictionReport,
    ConfidenceChain, ConfidenceStage,
    ReasoningProvenance, ProvenanceSnapshot,
    AuditQuery, AuditResult,
    CognitiveStats,
)
from app.cognitive.engine import (
    CognitiveTraceEngine, ReasoningReplayEngine,
    ConsistencyValidator, ContradictionDetector,
    ConfidencePropagator, AuditAPI,
    CognitiveValidationEngine,
    get_cognitive_engine, reset_cognitive_engine,
)

__all__ = [
    "CognitiveTraceEngine", "ReasoningReplayEngine",
    "ConsistencyValidator", "ContradictionDetector",
    "ConfidencePropagator", "AuditAPI",
    "CognitiveValidationEngine",
    "get_cognitive_engine", "reset_cognitive_engine",
    "ReasoningNode", "ReasoningGraph", "TraceConfig",
    "ReplayInput", "ReplayResult", "ReplayDiagnostic",
    "ConsistencyCheck", "ConsistencyResult",
    "Contradiction", "ContradictionReport",
    "ConfidenceChain", "ConfidenceStage",
    "ReasoningProvenance", "ProvenanceSnapshot",
    "AuditQuery", "AuditResult",
    "CognitiveStats",
]