"""SHUNYA Knowledge Graph — Canonical Node and Edge Families.

Implements the canonical family mappings defined in:
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §2.1 — Canonical node families
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.1 — Canonical edge families
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §3.4.5 — Edge type compatibility

Constitutional rules:
    - Every node belongs to exactly one family (§2.1).
    - Every edge belongs to exactly one family (§3.1).
    - Edge type must be valid for source and target node families (§3.4.5).
    - The Graph builds on the Kernel. The Kernel must never depend on the Graph.

Relationship ownership:
    - app/kernel/relationship.py → canonical lightweight API + compatibility layer, frozen
    - app/graph/EdgeStore → canonical persistence + execution layer for all new behaviour
    - No duplicate sources of truth.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from app.kernel.types import TypeRegistry, get_registry as get_type_registry


# ---------------------------------------------------------------------------
# Canonical node families (KG §2.1)
# ---------------------------------------------------------------------------

class NodeFamily(str, Enum):
    """Canonical node families derived from the Universal Type System (§2.1)."""
    PERSON = "person"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    CONVERSATION = "conversation"
    MEETING = "meeting"
    TASK = "task"
    COMMITMENT = "commitment"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"
    POLICY = "policy"
    PREDICTION = "prediction"
    EVIDENCE = "evidence"
    OBSERVATION = "observation"
    EVENT = "event"
    DECISION = "decision"
    OUTCOME = "outcome"
    EXECUTION = "execution"
    MEMORY = "memory"


# ---------------------------------------------------------------------------
# Canonical edge families (KG §3.1)
# ---------------------------------------------------------------------------

class EdgeFamily(str, Enum):
    """Canonical edge families (§3.1)."""
    OWNERSHIP = "ownership"
    MEMBERSHIP = "membership"
    DEPENDENCY = "dependency"
    REFERENCE = "reference"
    EVIDENTIAL = "evidential"
    CAUSAL = "causal"
    TEMPORAL = "temporal"
    DERIVATION = "derivation"
    HIERARCHICAL = "hierarchical"
    INHERITANCE = "inheritance"
    SOCIAL = "social"
    CONTEXTUAL = "contextual"
    PREDICTED = "predicted"
    HISTORICAL = "historical"
    ATTRIBUTION = "attribution"


# ---------------------------------------------------------------------------
# Family definitions
# ---------------------------------------------------------------------------

# Map each node family to its canonical ontology type root name
# (used to resolve the family for a given node_type via TypeRegistry hierarchy)
_NODE_FAMILY_TYPE_ROOTS: Dict[NodeFamily, str] = {
    NodeFamily.PERSON: "Person",
    NodeFamily.ORGANIZATION: "Organization",
    NodeFamily.DOCUMENT: "Document",
    NodeFamily.CONVERSATION: "Conversation",
    NodeFamily.MEETING: "Meeting",
    NodeFamily.TASK: "Task",
    NodeFamily.COMMITMENT: "Commitment",
    NodeFamily.WORKFLOW: "Workflow",
    NodeFamily.KNOWLEDGE: "Knowledge",
    NodeFamily.POLICY: "Policy",
    NodeFamily.PREDICTION: "Prediction",
    NodeFamily.EVIDENCE: "Evidence",
    NodeFamily.OBSERVATION: "Observation",
    NodeFamily.EVENT: "Event",
    NodeFamily.DECISION: "Decision",
    NodeFamily.OUTCOME: "Outcome",
    NodeFamily.EXECUTION: "Execution",
    NodeFamily.MEMORY: "Memory",
}

# Map each edge family to its concrete edge_type values
_EDGE_FAMILY_TYPES: Dict[EdgeFamily, List[str]] = {
    EdgeFamily.OWNERSHIP: ["owns", "created_by", "assigned_to"],
    EdgeFamily.MEMBERSHIP: ["belongs_to", "member_of", "works_at"],
    EdgeFamily.DEPENDENCY: ["depends_on", "requires", "blocks"],
    EdgeFamily.REFERENCE: ["mentions", "references", "cites"],
    EdgeFamily.EVIDENTIAL: ["supports", "contradicts", "proves"],
    EdgeFamily.CAUSAL: ["causes", "results_in", "leads_to"],
    EdgeFamily.TEMPORAL: ["precedes", "follows", "overlaps"],
    EdgeFamily.DERIVATION: ["derived_from", "inferred_from", "predicted_by"],
    EdgeFamily.HIERARCHICAL: ["contains", "parent_of", "supersedes"],
    EdgeFamily.INHERITANCE: ["inherits_from", "extends", "specializes"],
    EdgeFamily.SOCIAL: ["knows", "collaborates_with", "relates_to"],
    EdgeFamily.CONTEXTUAL: ["observed_in", "occurred_during", "relevant_to"],
    EdgeFamily.PREDICTED: ["predicted_by", "forecast_for"],
    EdgeFamily.HISTORICAL: ["superseded_by", "archived_from", "version_of"],
    EdgeFamily.ATTRIBUTION: ["attributed_to", "source_of", "originated_from"],
}

# Build reverse map: edge_type_value → EdgeFamily
_EDGE_TYPE_TO_FAMILY: Dict[str, EdgeFamily] = {}
for family, types in _EDGE_FAMILY_TYPES.items():
    for et in types:
        _EDGE_TYPE_TO_FAMILY[et] = family

# Edge family compatibility matrix (§3.4.5)
# Defined as (source_node_family, target_node_family) → list of valid edge families.
# Only restrictions are listed; unrestricted pairs accept all families.
# Format: (source_family, target_family) → set of valid EdgeFamily values
_EDGE_COMPATIBILITY: Dict[Tuple[str, str], Set[EdgeFamily]] = {
    # Membership: Person → Organization-like
    (NodeFamily.PERSON, NodeFamily.ORGANIZATION): {
        EdgeFamily.MEMBERSHIP, EdgeFamily.OWNERSHIP,
        EdgeFamily.REFERENCE, EdgeFamily.ATTRIBUTION,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
        EdgeFamily.EVIDENTIAL,
    },
    # Social: Person → Person only
    (NodeFamily.PERSON, NodeFamily.PERSON): {
        EdgeFamily.SOCIAL, EdgeFamily.OWNERSHIP,
        EdgeFamily.REFERENCE, EdgeFamily.ATTRIBUTION,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
        EdgeFamily.TEMPORAL, EdgeFamily.CAUSAL,
        EdgeFamily.EVIDENTIAL,
    },
    # Hierarchical: Organization → Organization, Document → Document
    (NodeFamily.ORGANIZATION, NodeFamily.ORGANIZATION): {
        EdgeFamily.HIERARCHICAL, EdgeFamily.MEMBERSHIP,
        EdgeFamily.OWNERSHIP, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
        EdgeFamily.DEPENDENCY,
    },
    (NodeFamily.DOCUMENT, NodeFamily.DOCUMENT): {
        EdgeFamily.HIERARCHICAL, EdgeFamily.REFERENCE,
        EdgeFamily.DERIVATION, EdgeFamily.CONTEXTUAL,
        EdgeFamily.HISTORICAL, EdgeFamily.DEPENDENCY,
        EdgeFamily.EVIDENTIAL,
    },
    # Commitment: Person → Commitment
    (NodeFamily.PERSON, NodeFamily.COMMITMENT): {
        EdgeFamily.OWNERSHIP, EdgeFamily.REFERENCE,
        EdgeFamily.ATTRIBUTION, EdgeFamily.CONTEXTUAL,
        EdgeFamily.HISTORICAL,
    },
    # Evidence: Evidence → anything
    (NodeFamily.EVIDENCE, NodeFamily.PERSON): {
        EdgeFamily.EVIDENTIAL, EdgeFamily.REFERENCE,
        EdgeFamily.ATTRIBUTION, EdgeFamily.CONTEXTUAL,
        EdgeFamily.HISTORICAL,
    },
    (NodeFamily.EVIDENCE, NodeFamily.DOCUMENT): {
        EdgeFamily.EVIDENTIAL, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
    },
    # Prediction: Prediction → target
    (NodeFamily.PREDICTION, NodeFamily.PERSON): {
        EdgeFamily.PREDICTED, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL,
    },
    (NodeFamily.PREDICTION, NodeFamily.EVENT): {
        EdgeFamily.PREDICTED, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL, EdgeFamily.CAUSAL,
    },
    # Inheritance: constitutional only, not stored as graph edges
    (NodeFamily.POLICY, NodeFamily.POLICY): {
        EdgeFamily.HIERARCHICAL, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
    },
    # Ownership: Person/Organization → anything
    (NodeFamily.PERSON, NodeFamily.DOCUMENT): {
        EdgeFamily.OWNERSHIP, EdgeFamily.REFERENCE,
        EdgeFamily.ATTRIBUTION, EdgeFamily.CONTEXTUAL,
        EdgeFamily.HISTORICAL, EdgeFamily.EVIDENTIAL,
    },
    (NodeFamily.ORGANIZATION, NodeFamily.DOCUMENT): {
        EdgeFamily.OWNERSHIP, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
    },
    # Execution: links to its outcome
    (NodeFamily.EXECUTION, NodeFamily.OUTCOME): {
        EdgeFamily.CAUSAL, EdgeFamily.REFERENCE,
        EdgeFamily.CONTEXTUAL, EdgeFamily.HISTORICAL,
    },
    # Event → Decision/Outcome
    (NodeFamily.EVENT, NodeFamily.DECISION): {
        EdgeFamily.CAUSAL, EdgeFamily.TEMPORAL,
        EdgeFamily.REFERENCE, EdgeFamily.CONTEXTUAL,
        EdgeFamily.HISTORICAL,
    },
    (NodeFamily.EVENT, NodeFamily.OUTCOME): {
        EdgeFamily.CAUSAL, EdgeFamily.TEMPORAL,
        EdgeFamily.REFERENCE, EdgeFamily.CONTEXTUAL,
        EdgeFamily.HISTORICAL,
    },
}

# Families that are universally compatible (any source → any target)
_UNIVERSAL_FAMILIES: Set[EdgeFamily] = {
    EdgeFamily.REFERENCE,
    EdgeFamily.CONTEXTUAL,
    EdgeFamily.HISTORICAL,
    EdgeFamily.TEMPORAL,
    EdgeFamily.EVIDENTIAL,
}


# ---------------------------------------------------------------------------
# Family resolution
# ---------------------------------------------------------------------------

class Families:
    """Registry and resolver for canonical node and edge families.

    Provides type-to-family mapping, family membership checks, and
    edge type compatibility validation (§3.4.5).
    """

    @staticmethod
    def get_node_family(node_type: str) -> Optional[NodeFamily]:
        """Resolve the canonical family for a node type.

        Uses the TypeRegistry to walk the type hierarchy. If the type
        or any ancestor matches a family root, that family is returned.

        Args:
            node_type: A type name from the Universal Type System.

        Returns:
            The NodeFamily, or None if the type is unknown.
        """
        registry = get_type_registry()
        # Walk the type hierarchy
        current = node_type
        seen: Set[str] = set()
        # Build reverse map: root type name -> NodeFamily
        family_by_root: Dict[str, NodeFamily] = {
            root: family for family, root in _NODE_FAMILY_TYPE_ROOTS.items()
        }

        while current and current not in seen:
            seen.add(current)
            if current in family_by_root:
                return family_by_root[current]
            # Walk up to parent
            node = registry.get(current)
            if node is None:
                return None
            current = node.parent

        return None

    @staticmethod
    def get_node_families() -> List[NodeFamily]:
        """Get all canonical node families."""
        return list(NodeFamily)

    @staticmethod
    def get_node_family_root(node_family: NodeFamily) -> str:
        """Get the canonical type root for a node family."""
        return _NODE_FAMILY_TYPE_ROOTS.get(node_family, "")

    @staticmethod
    def get_edge_family(edge_type: str) -> Optional[EdgeFamily]:
        """Resolve the canonical family for an edge type value.

        Args:
            edge_type: A concrete edge type string (e.g., 'knows', 'owns').

        Returns:
            The EdgeFamily, or None if the edge type is unknown.
        """
        return _EDGE_TYPE_TO_FAMILY.get(edge_type)

    @staticmethod
    def get_edge_types(family: EdgeFamily) -> List[str]:
        """Get all concrete edge type values for a family."""
        return list(_EDGE_FAMILY_TYPES.get(family, []))

    @staticmethod
    def get_edge_families() -> List[EdgeFamily]:
        """Get all canonical edge families."""
        return list(EdgeFamily)

    @staticmethod
    def get_all_edge_types() -> List[str]:
        """Get all known concrete edge type values."""
        return list(_EDGE_TYPE_TO_FAMILY.keys())

    @staticmethod
    def is_valid_edge_type(edge_type: str) -> bool:
        """Check if an edge type belongs to a known canonical family."""
        return edge_type in _EDGE_TYPE_TO_FAMILY

    @staticmethod
    def validate_edge_compatibility(
        source_node_type: str,
        target_node_type: str,
        edge_type: str,
    ) -> Tuple[bool, str]:
        """Validate that an edge type is compatible with source/target node types.

        Implements §3.4.5: Edge type is valid for source and target types.

        Args:
            source_node_type: The type of the source node.
            target_node_type: The type of the target node.
            edge_type: The concrete edge type value.

        Returns:
            A tuple of (is_valid, reason_message).
            If valid, reason is empty.
            If invalid, reason describes the incompatibility.
        """
        # Resolve families
        source_family = Families.get_node_family(source_node_type)
        target_family = Families.get_node_family(target_node_type)
        edge_family = Families.get_edge_family(edge_type)

        if edge_family is None:
            return False, f"Unknown edge type '{edge_type}'"

        if source_family is None:
            return False, f"Unknown source node type '{source_node_type}'"

        if target_family is None:
            return False, f"Unknown target node type '{target_node_type}'"

        # Universal families are always compatible
        if edge_family in _UNIVERSAL_FAMILIES:
            return True, ""

        # Check explicit compatibility matrix
        key = (source_family, target_family)
        if key in _EDGE_COMPATIBILITY:
            allowed = _EDGE_COMPATIBILITY[key]
            if edge_family in allowed:
                return True, ""
            allowed_names = sorted(f.value for f in allowed)
            return False, (
                f"Edge type '{edge_type}' (family '{edge_family.value}') "
                f"is not compatible with {source_family.value} → "
                f"{target_family.value}. Allowed families: {allowed_names}"
            )

        # No explicit restriction — assume compatible
        return True, ""

    @staticmethod
    def get_valid_edge_types(
        source_node_type: str,
        target_node_type: str,
    ) -> List[str]:
        """Get all edge types valid between two node types.

        Args:
            source_node_type: The type of the source node.
            target_node_type: The type of the target node.

        Returns:
            List of valid edge type strings.
        """
        source_family = Families.get_node_family(source_node_type)
        target_family = Families.get_node_family(target_node_type)

        if source_family is None or target_family is None:
            return []

        valid: List[str] = []
        for edge_type, family in _EDGE_TYPE_TO_FAMILY.items():
            is_valid, _ = Families.validate_edge_compatibility(
                source_node_type, target_node_type, edge_type
            )
            if is_valid:
                valid.append(edge_type)

        return valid


# ---------------------------------------------------------------------------
# Convenience sets
# ---------------------------------------------------------------------------

ALL_NODE_FAMILIES: List[NodeFamily] = list(NodeFamily)
ALL_EDGE_FAMILIES: List[EdgeFamily] = list(EdgeFamily)
ALL_EDGE_TYPES: List[str] = list(_EDGE_TYPE_TO_FAMILY.keys())