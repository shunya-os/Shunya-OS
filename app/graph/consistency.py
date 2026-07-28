"""
SHUNYA Knowledge Graph — Graph Validator (E-003-MOD-004).

Implements deterministic, side-effect-free validation of graph correctness
as defined in:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4 — Edge validation
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.4  — Identity
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.6  — Types
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.9  — Confidence
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §1.10 — Versioning
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §13.2 — Visibility

Constitutional rules:
    - Validation is read-only. Never mutates nodes, edges, or stores.
    - Validation is deterministic. Same graph always produces same result.
    - Every Node identity is permanent, unique, never reused (§1.4).
    - Node type is immutable after creation (§1.6).
    - Every Edge has valid source and target Nodes (§3.2.1).
    - No two Edges share the same (source, target, type) triple (§3.2.3).
    - Edge type must be valid for source and target node families (§3.4.5).
    - Confidence is always 0.0–1.0 (§1.9).
    - Version is always >= 1 (§1.10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.graph.node import (
    Node, NodeStore, VisibilityLevel, NodeStatus,
)
from app.graph.edge import (
    Edge, EdgeStore, EdgeDirection, EdgeStatus,
)
from app.graph.families import Families
from app.kernel.types import get_registry as get_type_registry


# ---------------------------------------------------------------------------
# ValidationResult — structured output of a validation pass
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    """A single validation error.

    Attributes:
        code: Machine-readable error code (e.g. 'E-NODE-001').
        message: Human-readable description of the violation.
        node_id: Node identity the error relates to, or empty string.
        edge_triple: Edge triple the error relates to, or None.
        severity: 'error' (blocking) or 'warning' (advisory).
    """
    code: str
    message: str
    node_id: str = ""
    edge_triple: Optional[Tuple[str, str, str]] = None
    severity: str = "error"


@dataclass
class ValidationResult:
    """Structured result of a graph validation pass.

    Attributes:
        errors: List of ValidationError instances (blocking).
        warnings: List of ValidationError instances (advisory).
        node_count: Number of nodes examined.
        edge_count: Number of edges examined.
        summary: Human-readable one-line summary.
    """
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0

    @property
    def is_valid(self) -> bool:
        """True if no errors were found (warnings do not invalidate)."""
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def summary(self) -> str:
        parts = []
        if self.is_valid:
            parts.append("VALID")
        else:
            parts.append(f"INVALID ({self.error_count} error(s))")
        parts.append(f"{self.node_count} node(s)")
        parts.append(f"{self.edge_count} edge(s)")
        if self.warnings:
            parts.append(f"{self.warning_count} warning(s)")
        return " — ".join(parts)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another ValidationResult into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.node_count += other.node_count
        self.edge_count += other.edge_count
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a canonical dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "summary": self.summary,
            "errors": [
                {
                    "code": e.code,
                    "message": e.message,
                    "node_id": e.node_id,
                    "edge_triple": list(e.edge_triple) if e.edge_triple else None,
                    "severity": e.severity,
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "code": w.code,
                    "message": w.message,
                    "node_id": w.node_id,
                    "edge_triple": list(w.edge_triple) if w.edge_triple else None,
                    "severity": w.severity,
                }
                for w in self.warnings
            ],
        }


# ---------------------------------------------------------------------------
# Validation error codes
# ---------------------------------------------------------------------------

# Node-level errors
E_NODE_ID_EMPTY = "E-NODE-001"
E_NODE_ID_FORMAT = "E-NODE-002"
E_NODE_TYPE_UNKNOWN = "E-NODE-003"
E_NODE_CONFIDENCE_RANGE = "E-NODE-004"
E_NODE_VERSION_LT_ONE = "E-NODE-005"
E_NODE_STATUS_INVALID = "E-NODE-006"
E_NODE_VISIBILITY_INVALID = "E-NODE-007"
E_NODE_CONFIDENCE_NEGATIVE = "E-NODE-008"

# Edge-level errors
E_EDGE_TRIPLE_DUPLICATE = "E-EDGE-001"
E_EDGE_SOURCE_MISSING = "E-EDGE-002"
E_EDGE_TARGET_MISSING = "E-EDGE-003"
E_EDGE_TYPE_UNKNOWN = "E-EDGE-004"
E_EDGE_CONFIDENCE_RANGE = "E-EDGE-005"
E_EDGE_DIRECTION_INVALID = "E-EDGE-006"
E_EDGE_STATUS_INVALID = "E-EDGE-007"
E_EDGE_TYPE_INCOMPATIBLE = "E-EDGE-008"
E_EDGE_CONFIDENCE_NEGATIVE = "E-EDGE-009"

# Graph-wide invariant errors
E_INV_ORPHAN_NODE = "E-INV-001"
E_INV_ORPHAN_EDGE_SOURCE = "E-INV-002"
E_INV_ORPHAN_EDGE_TARGET = "E-INV-003"
E_INV_NODE_ID_DUPLICATE = "E-INV-004"

# Warnings
W_NODE_NO_LABELS = "W-NODE-001"
W_NODE_NO_OWNER = "W-NODE-002"
W_NODE_NO_EVIDENCE = "W-NODE-003"
W_EDGE_NO_EVIDENCE = "W-EDGE-001"
W_EDGE_LOW_CONFIDENCE = "W-EDGE-002"
W_EDGE_ZERO_WEIGHT = "W-EDGE-003"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_VALID_NODE_STATUSES: List[str] = [s.value for s in NodeStatus]
_VALID_VISIBILITY_LEVELS: List[str] = [v.value for v in VisibilityLevel]
_VALID_EDGE_DIRECTIONS: List[str] = [d.value for d in EdgeDirection]
_VALID_EDGE_STATUSES: List[str] = [s.value for s in EdgeStatus]

# Node ID format: n_<hex timestamp><hex random>
# Minimum reasonable length for a generated ID
_MIN_NODE_ID_LENGTH = 8


def _has_node_id_format(node_id: str) -> bool:
    """Check if a node_id has the expected format (n_ prefix with hex suffix)."""
    if not node_id.startswith("n_"):
        return False
    if len(node_id) < _MIN_NODE_ID_LENGTH:
        return False
    # The portion after n_ should be hex characters
    hex_part = node_id[2:]
    # n_ followed by at least one alphanumeric character
    return len(hex_part) > 0


def _count_edges_per_triple(edges: Sequence[Edge]) -> Dict[Tuple[str, str, str], int]:
    """Count occurrences of each (source, target, type) triple."""
    counts: Dict[Tuple[str, str, str], int] = {}
    for edge in edges:
        key = edge.triple
        counts[key] = counts.get(key, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# GraphValidator — main validation class
# ---------------------------------------------------------------------------


class GraphValidator:
    """Deterministic, side-effect-free graph validator.

    Evaluates the correctness of a Knowledge Graph (nodes + edges) and
    produces a structured ValidationResult. Never mutates the graph.

    Usage:
        validator = GraphValidator(node_store, edge_store)
        result = validator.validate_all()
        # or run specific checks:
        node_result = validator.validate_nodes()
        edge_result = validator.validate_edges()
        invariant_result = validator.validate_invariants()
    """

    def __init__(
        self,
        node_store: Optional[NodeStore] = None,
        edge_store: Optional[EdgeStore] = None,
    ):
        from app.graph.node import get_node_store
        from app.graph.edge import get_edge_store

        self._node_store = node_store or get_node_store()
        self._edge_store = edge_store or get_edge_store()

    # ---- Public API --------------------------------------------------------

    def validate_all(self) -> ValidationResult:
        """Run all validations: nodes, edges, and invariants.

        Returns a single merged ValidationResult.
        """
        result = ValidationResult()
        result.merge(self.validate_nodes())
        result.merge(self.validate_edges())
        result.merge(self.validate_invariants())
        # Set counts from the store once to avoid cumulative addition
        result.node_count = self._node_store.count()
        result.edge_count = self._edge_store.count()
        return result

    def validate_nodes(
        self,
        nodes: Optional[Sequence[Node]] = None,
    ) -> ValidationResult:
        """Validate every Node in the store (or a provided sequence).

        Checks:
            - Identity is non-empty and has valid format
            - Type is registered in the Universal Type System
            - Confidence is 0.0–1.0
            - Version is >= 1
            - Status is a known NodeStatus value
            - Visibility is a known VisibilityLevel value
        """
        result = ValidationResult()
        target_nodes = list(nodes) if nodes is not None else self._node_store.all()

        result.node_count = len(target_nodes)

        for node in target_nodes:
            self._validate_node(node, result)

        return result

    def validate_edges(
        self,
        edges: Optional[Sequence[Edge]] = None,
    ) -> ValidationResult:
        """Validate every Edge in the store (or a provided sequence).

        Checks:
            - Source and target Nodes exist in the store
            - Edge type is a known canonical type
            - Edge type is compatible with source/target node families
            - Confidence is 0.0–1.0
            - Direction is a known EdgeDirection value
            - Status is a known EdgeStatus value
        """
        result = ValidationResult()
        target_edges = list(edges) if edges is not None else self._edge_store.all()

        result.edge_count = len(target_edges)

        # Build node existence set for O(1) lookups
        existing_node_ids: set[str] = set()
        for node in self._node_store.all():
            existing_node_ids.add(node.node_id)

        # Check triple uniqueness across all edges
        triple_counts = _count_edges_per_triple(target_edges)

        for edge in target_edges:
            self._validate_edge(edge, result, existing_node_ids, triple_counts)

        return result

    def validate_invariants(
        self,
        nodes: Optional[Sequence[Node]] = None,
        edges: Optional[Sequence[Edge]] = None,
    ) -> ValidationResult:
        """Validate graph-wide invariants.

        Checks:
            - No orphan edges (edges whose source or target no longer exist)
            - No duplicate node IDs
        """
        result = ValidationResult()
        target_nodes = list(nodes) if nodes is not None else self._node_store.all()
        target_edges = list(edges) if edges is not None else self._edge_store.all()

        result.node_count = len(target_nodes)
        result.edge_count = len(target_edges)

        # Node ID uniqueness check
        node_ids: Dict[str, int] = {}
        for node in target_nodes:
            node_ids[node.node_id] = node_ids.get(node.node_id, 0) + 1
        for nid, count in node_ids.items():
            if count > 1:
                result.errors.append(ValidationError(
                    code=E_INV_NODE_ID_DUPLICATE,
                    message=f"Node ID '{nid[:24]}...' appears {count} times. "
                            "Node identity must be unique (§1.4).",
                    node_id=nid,
                ))

        # Build existence sets
        existing_node_ids = set(node_ids.keys())

        # Orphan edges
        for edge in target_edges:
            if edge.source_id not in existing_node_ids:
                result.errors.append(ValidationError(
                    code=E_INV_ORPHAN_EDGE_SOURCE,
                    message=f"Edge references non-existent source Node "
                            f"'{edge.short_source}'. Every Edge must have a "
                            f"valid source (§3.2.1).",
                    edge_triple=edge.triple,
                ))
            if edge.target_id not in existing_node_ids:
                result.errors.append(ValidationError(
                    code=E_INV_ORPHAN_EDGE_TARGET,
                    message=f"Edge references non-existent target Node "
                            f"'{edge.short_target}'. Every Edge must have a "
                            f"valid target (§3.2.1).",
                    edge_triple=edge.triple,
                ))

        return result

    # ---- Node validation ---------------------------------------------------

    def _validate_node(self, node: Node, result: ValidationResult) -> None:
        """Validate a single Node and append errors/warnings to result."""
        # E-NODE-001: Identity must not be empty
        if not node.node_id:
            result.errors.append(ValidationError(
                code=E_NODE_ID_EMPTY,
                message="Node identity is empty. Every Node must have a "
                        "permanent, unique identity (§1.4).",
            ))

        # E-NODE-002: Identity format
        elif not _has_node_id_format(node.node_id):
            result.warnings.append(ValidationError(
                code=E_NODE_ID_FORMAT,
                message=f"Node ID '{node.short_id}' does not match "
                        f"expected 'n_<hex>' format.",
                node_id=node.node_id,
                severity="warning",
            ))

        # E-NODE-003: Type must be registered
        registry = get_type_registry()
        type_node = registry.get(node.node_type)
        if type_node is None:
            result.errors.append(ValidationError(
                code=E_NODE_TYPE_UNKNOWN,
                message=f"Node type '{node.node_type}' is not registered "
                        f"in the Universal Type System. Every Node must have "
                        f"a valid type (§1.6).",
                node_id=node.node_id,
            ))

        # E-NODE-004: Confidence must be 0.0–1.0
        if node.confidence < 0.0:
            result.errors.append(ValidationError(
                code=E_NODE_CONFIDENCE_NEGATIVE,
                message=f"Node confidence {node.confidence} is negative. "
                        f"Confidence must be 0.0–1.0 (§1.9).",
                node_id=node.node_id,
            ))
        elif node.confidence > 1.0:
            result.errors.append(ValidationError(
                code=E_NODE_CONFIDENCE_RANGE,
                message=f"Node confidence {node.confidence} exceeds 1.0. "
                        f"Confidence must be 0.0–1.0 (§1.9).",
                node_id=node.node_id,
            ))

        # E-NODE-005: Version must be >= 1
        if node.version < 1:
            result.errors.append(ValidationError(
                code=E_NODE_VERSION_LT_ONE,
                message=f"Node version {node.version} is less than 1. "
                        f"Version must be >= 1 (§1.10).",
                node_id=node.node_id,
            ))

        # E-NODE-006: Status must be valid
        if node.status not in _VALID_NODE_STATUSES:
            result.errors.append(ValidationError(
                code=E_NODE_STATUS_INVALID,
                message=f"Node status '{node.status}' is not a valid "
                        f"NodeStatus value. Valid: {_VALID_NODE_STATUSES}.",
                node_id=node.node_id,
            ))

        # E-NODE-007: Visibility must be valid
        if node.visibility not in _VALID_VISIBILITY_LEVELS:
            result.errors.append(ValidationError(
                code=E_NODE_VISIBILITY_INVALID,
                message=f"Node visibility '{node.visibility}' is not a valid "
                        f"VisibilityLevel value. Valid: {_VALID_VISIBILITY_LEVELS}.",
                node_id=node.node_id,
            ))

        # Warnings
        if not node.labels:
            result.warnings.append(ValidationError(
                code=W_NODE_NO_LABELS,
                message=f"Node '{node.short_id}' has no labels. "
                        f"Labels improve discoverability (§1.5).",
                node_id=node.node_id,
                severity="warning",
            ))
        if not node.owner_id:
            result.warnings.append(ValidationError(
                code=W_NODE_NO_OWNER,
                message=f"Node '{node.short_id}' has no owner. "
                        f"Ownership clarifies responsibility (§13.3).",
                node_id=node.node_id,
                severity="warning",
            ))
        if not node.evidence:
            result.warnings.append(ValidationError(
                code=W_NODE_NO_EVIDENCE,
                message=f"Node '{node.short_id}' has no evidence chain. "
                        f"Evidence provides traceability.",
                node_id=node.node_id,
                severity="warning",
            ))

    # ---- Edge validation ---------------------------------------------------

    def _validate_edge(
        self,
        edge: Edge,
        result: ValidationResult,
        existing_node_ids: set[str],
        triple_counts: Dict[Tuple[str, str, str], int],
    ) -> None:
        """Validate a single Edge and append errors/warnings to result."""
        # E-EDGE-001: Triple uniqueness
        triple_count = triple_counts.get(edge.triple, 0)
        if triple_count > 1:
            result.errors.append(ValidationError(
                code=E_EDGE_TRIPLE_DUPLICATE,
                message=f"Duplicate Edge triple ({edge.short_source}, "
                        f"{edge.short_target}, {edge.edge_type}). "
                        f"Appears {triple_count} times. "
                        f"No two Edges may share the same triple (§3.2.3).",
                edge_triple=edge.triple,
            ))

        # E-EDGE-002: Source node must exist
        if edge.source_id not in existing_node_ids:
            result.errors.append(ValidationError(
                code=E_EDGE_SOURCE_MISSING,
                message=f"Source Node '{edge.short_source}' not found "
                        f"in the graph. Every Edge must have a valid "
                        f"source Node (§3.2.1).",
                edge_triple=edge.triple,
            ))

        # E-EDGE-003: Target node must exist
        if edge.target_id not in existing_node_ids:
            result.errors.append(ValidationError(
                code=E_EDGE_TARGET_MISSING,
                message=f"Target Node '{edge.short_target}' not found "
                        f"in the graph. Every Edge must have a valid "
                        f"target Node (§3.2.1).",
                edge_triple=edge.triple,
            ))

        # E-EDGE-004: Edge type must be known
        if not Families.is_valid_edge_type(edge.edge_type):
            result.errors.append(ValidationError(
                code=E_EDGE_TYPE_UNKNOWN,
                message=f"Edge type '{edge.edge_type}' is not a known "
                        f"canonical edge type.",
                edge_triple=edge.triple,
            ))

        # E-EDGE-005: Confidence must be 0.0–1.0
        if edge.confidence < 0.0:
            result.errors.append(ValidationError(
                code=E_EDGE_CONFIDENCE_NEGATIVE,
                message=f"Edge confidence {edge.confidence} is negative. "
                        f"Confidence must be 0.0–1.0 (§1.9).",
                edge_triple=edge.triple,
            ))
        elif edge.confidence > 1.0:
            result.errors.append(ValidationError(
                code=E_EDGE_CONFIDENCE_RANGE,
                message=f"Edge confidence {edge.confidence} exceeds 1.0. "
                        f"Confidence must be 0.0–1.0 (§1.9).",
                edge_triple=edge.triple,
            ))

        # E-EDGE-006: Direction must be valid
        if edge.direction not in _VALID_EDGE_DIRECTIONS:
            result.errors.append(ValidationError(
                code=E_EDGE_DIRECTION_INVALID,
                message=f"Edge direction '{edge.direction}' is not a valid "
                        f"EdgeDirection value. Valid: {_VALID_EDGE_DIRECTIONS}.",
                edge_triple=edge.triple,
            ))

        # E-EDGE-007: Status must be valid
        if edge.status not in _VALID_EDGE_STATUSES:
            result.errors.append(ValidationError(
                code=E_EDGE_STATUS_INVALID,
                message=f"Edge status '{edge.status}' is not a valid "
                        f"EdgeStatus value. Valid: {_VALID_EDGE_STATUSES}.",
                edge_triple=edge.triple,
            ))

        # E-EDGE-008: Edge type compatibility
        if len(edge.source_id) > 0 and len(edge.target_id) > 0 and Families.is_valid_edge_type(edge.edge_type):
            source_node = self._node_store.get(edge.source_id)
            target_node = self._node_store.get(edge.target_id)
            if source_node and target_node:
                is_compat, reason = Families.validate_edge_compatibility(
                    source_node.node_type, target_node.node_type, edge.edge_type,
                )
                if not is_compat:
                    result.errors.append(ValidationError(
                        code=E_EDGE_TYPE_INCOMPATIBLE,
                        message=f"Edge type incompatibility: {reason} (§3.4.5).",
                        edge_triple=edge.triple,
                    ))

        # Warnings
        if not edge.evidence:
            result.warnings.append(ValidationError(
                code=W_EDGE_NO_EVIDENCE,
                message=f"Edge ({edge.short_source}, {edge.short_target}, "
                        f"{edge.edge_type}) has no evidence chain.",
                edge_triple=edge.triple,
                severity="warning",
            ))
        if edge.confidence <= 0.3:
            result.warnings.append(ValidationError(
                code=W_EDGE_LOW_CONFIDENCE,
                message=f"Edge confidence {edge.confidence} is very low "
                        f"(≤ 0.3). Consider reviewing the evidence chain.",
                edge_triple=edge.triple,
                severity="warning",
            ))
        if edge.weight <= 0.0:
            result.warnings.append(ValidationError(
                code=W_EDGE_ZERO_WEIGHT,
                message=f"Edge weight is {edge.weight}. Zero-weight edges "
                        f"may indicate a configuration error.",
                edge_triple=edge.triple,
                severity="warning",
            ))

    # ---- Warming helpers ---------------------------------------------------

    def _check_node_warnings(
        self,
        nodes: Sequence[Node],
        result: ValidationResult,
    ) -> None:
        """Emit warnings for nodes missing optional but recommended fields."""
        for node in nodes:
            if not node.labels:
                result.warnings.append(ValidationError(
                    code=W_NODE_NO_LABELS,
                    message=f"Node '{node.short_id}' has no labels. "
                            f"Labels improve discoverability (§1.5).",
                    node_id=node.node_id,
                    severity="warning",
                ))
            if not node.owner_id:
                result.warnings.append(ValidationError(
                    code=W_NODE_NO_OWNER,
                    message=f"Node '{node.short_id}' has no owner. "
                            f"Ownership clarifies responsibility (§13.3).",
                    node_id=node.node_id,
                    severity="warning",
                ))
            if not node.evidence:
                result.warnings.append(ValidationError(
                    code=W_NODE_NO_EVIDENCE,
                    message=f"Node '{node.short_id}' has no evidence chain. "
                            f"Evidence provides traceability.",
                    node_id=node.node_id,
                    severity="warning",
                ))

    def _check_edge_warnings(
        self,
        edges: Sequence[Edge],
        result: ValidationResult,
    ) -> None:
        """Emit warnings for edges missing optional but recommended fields."""
        for edge in edges:
            if not edge.evidence:
                result.warnings.append(ValidationError(
                    code=W_EDGE_NO_EVIDENCE,
                    message=f"Edge ({edge.short_source}, {edge.short_target}, "
                            f"{edge.edge_type}) has no evidence chain.",
                    edge_triple=edge.triple,
                    severity="warning",
                ))
            if edge.confidence <= 0.3:
                result.warnings.append(ValidationError(
                    code=W_EDGE_LOW_CONFIDENCE,
                    message=f"Edge confidence {edge.confidence} is very low "
                            f"(≤ 0.3). Consider reviewing the evidence chain.",
                    edge_triple=edge.triple,
                    severity="warning",
                ))
            if edge.weight <= 0.0:
                result.warnings.append(ValidationError(
                    code=W_EDGE_ZERO_WEIGHT,
                    message=f"Edge weight is {edge.weight}. Zero-weight edges "
                            f"may indicate a configuration error.",
                    edge_triple=edge.triple,
                    severity="warning",
                ))

    # ---- Batch validation helpers ------------------------------------------

    def validate_node(self, node: Node) -> ValidationResult:
        """Validate a single Node. Convenience wrapper."""
        return self.validate_nodes(nodes=[node])

    def validate_edge(self, edge: Edge) -> ValidationResult:
        """Validate a single Edge. Convenience wrapper."""
        return self.validate_edges(edges=[edge])

    def validate_node_by_id(self, node_id: str) -> ValidationResult:
        """Validate a single Node by its identity.

        Returns an invalid result if the Node is not found.
        """
        node = self._node_store.get(node_id)
        if node is None:
            result = ValidationResult()
            result.errors.append(ValidationError(
                code=E_NODE_ID_EMPTY,
                message=f"Node '{node_id[:24]}...' not found in the graph.",
            ))
            return result
        return self.validate_node(node)