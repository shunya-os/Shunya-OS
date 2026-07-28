"""
SHUNYA Object Registry — Object Registry and Protocol Compliance Checker

The ObjectRegistry manages type registration, object discovery, and
protocol compliance verification. The ProtocolComplianceChecker
validates that objects implement all 15 mandatory sections of the
Universal Object Protocol.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import (
    ComplianceReport,
    ObjectMetadata,
)

# =========================================================================
# Type Hierarchy Support
# =========================================================================


class TypeHierarchy:
    """Manages parent/child type relationships and abstract type checking.

    Types form a DAG where each type can have at most one parent
    (single-inheritance model). Abstract types cannot have direct
    instances.
    """

    def __init__(self) -> None:
        self._parents: dict[str, str | None] = {}  # type → parent
        self._children: dict[str, set[str]] = {}  # type → set of child types
        self._abstract: set[str] = set()

    def add_type(
        self,
        type_name: str,
        parent_type: str | None = None,
        is_abstract: bool = False,
    ) -> None:
        """Register a type in the hierarchy.

        Args:
            type_name: Type identifier.
            parent_type: Optional parent type name.
            is_abstract: If True, this type cannot have direct instances.

        Raises:
            ValueError: If parent_type does not exist, or if the
                        addition would create a cycle.
        """
        if parent_type and parent_type not in self._parents:
            raise ValueError(
                f"Parent type '{parent_type}' is not registered in the hierarchy."
            )

        self._parents[type_name] = parent_type
        self._children.setdefault(type_name, set())

        if parent_type:
            self._children.setdefault(parent_type, set()).add(type_name)

        if is_abstract:
            self._abstract.add(type_name)

    def get_parent(self, type_name: str) -> str | None:
        """Return the parent type, or None if it has no parent."""
        return self._parents.get(type_name)

    def get_children(self, type_name: str) -> set[str]:
        """Return the set of direct child type names."""
        return set(self._children.get(type_name, set()))

    def get_descendants(self, type_name: str) -> set[str]:
        """Return all descendant type names (children, grandchildren, etc.)."""
        descendants: set[str] = set()
        to_visit = list(self._children.get(type_name, set()))
        while to_visit:
            child = to_visit.pop()
            if child not in descendants:
                descendants.add(child)
                to_visit.extend(self._children.get(child, set()))
        return descendants

    def get_ancestors(self, type_name: str) -> list[str]:
        """Return the lineage from the root ancestor down to type_name.

        Returns a list where the first element is the root ancestor
        and the last is type_name itself.
        """
        lineage: list[str] = []
        cur: str | None = type_name
        while cur:
            lineage.append(cur)
            cur = self._parents.get(cur)
        lineage.reverse()
        return lineage

    def is_abstract(self, type_name: str) -> bool:
        """Check if a type is abstract."""
        return type_name in self._abstract

    def is_subtype_of(self, type_name: str, potential_parent: str) -> bool:
        """Check if type_name is a descendant of potential_parent."""
        return potential_parent in self.get_ancestors(type_name)

    def has_type(self, type_name: str) -> bool:
        """Check if a type is registered."""
        return type_name in self._parents

    def remove_type(self, type_name: str) -> None:
        """Remove a type from the hierarchy.

        The caller must ensure children have been removed first.

        Args:
            type_name: Type to remove.

        Raises:
            KeyError: If the type is not registered.
            ValueError: If the type still has children.
        """
        if type_name not in self._parents:
            raise KeyError(f"Type '{type_name}' is not in the hierarchy.")

        children = self._children.get(type_name, set())
        if children:
            raise ValueError(
                f"Cannot remove '{type_name}': it has child type(s): "
                f"{', '.join(sorted(children))}. Remove children first."
            )

        # Remove from parent's children list
        parent = self._parents[type_name]
        if parent and type_name in self._children.get(parent, set()):
            self._children[parent].discard(type_name)

        del self._parents[type_name]
        self._children.pop(type_name, None)
        self._abstract.discard(type_name)

    @property
    def count(self) -> int:
        """Number of registered types."""
        return len(self._parents)

    def to_dict(self) -> dict[str, Any]:
        """Serialize hierarchy for diagnostics."""
        return {
            "types": {
                t: {
                    "parent": self._parents[t],
                    "children": sorted(self._children.get(t, set())),
                    "abstract": t in self._abstract,
                }
                for t in sorted(self._parents.keys())
            }
        }


# =========================================================================
# Object Registry
# =========================================================================


class ObjectRegistry:
    """Central registry for object types and instances in the SHUNYA runtime.

    Responsibilities:
    - Type registration, unregistration, and listing
    - Type hierarchy management (parent/child, abstract types)
    - Object discovery by type, id, or field value
    - Metadata retrieval for registered objects
    - Protocol compliance verification via ProtocolComplianceChecker
    - Version compatibility checks

    This is NOT a persistence layer — it tracks type metadata and
    in-memory object references for discovery purposes.
    """

    def __init__(self) -> None:
        self._types: dict[str, type[Any]] = {}  # type_name → Python class
        self._type_metadata: dict[str, ObjectMetadata] = {}  # type_name → metadata
        self._objects: dict[str, dict[str, Any]] = {}  # type_name → {obj_id: obj}
        self._hierarchy = TypeHierarchy()

        # Optional: a callable that returns True if an object
        # implements the Universal Object Protocol (used for runtime
        # type checking at registration time when objects are passed).
        self._compliance_checker: ProtocolComplianceChecker | None = None

    # ------------------------------------------------------------------
    # Type Registration
    # ------------------------------------------------------------------

    def register_type(
        self,
        type_class: type[Any],
        *,
        type_name: str | None = None,
        version: str = "1.0.0",
        description: str = "",
        parent_type: str | None = None,
        is_abstract: bool = False,
        min_compatible_version: str = "1.0.0",
    ) -> None:
        """Register a type class with the registry.

        Args:
            type_class: The Python class for this object type.
            type_name: Optional override for the type name (defaults to
                       the class name in snake_case).
            version: Semantic version string.
            description: Human-readable description.
            parent_type: Optional parent type name.
            is_abstract: If True, no direct instances.
            min_compatible_version: Minimum backward-compatible version.

        Raises:
            ValueError: If the type is already registered, or if the
                        parent type references a non-existent type.
        """
        name = (type_name or type_class.__name__).lower()

        if name in self._types:
            raise ValueError(
                f"Type '{name}' is already registered. "
                f"Use unregister_type first to re-register."
            )

        # If a parent type is specified, it must exist or be being registered now
        if parent_type and parent_type not in self._types:
            raise ValueError(
                f"Cannot register '{name}' with parent '{parent_type}': "
                f"parent type is not registered."
            )

        self._types[name] = type_class
        self._objects.setdefault(name, {})

        meta = ObjectMetadata(
            type_name=name,
            version=version,
            description=description,
            parent_type=parent_type,
            is_abstract=is_abstract,
            min_compatible_version=min_compatible_version,
        )
        self._type_metadata[name] = meta
        self._hierarchy.add_type(name, parent_type=parent_type, is_abstract=is_abstract)

    def unregister_type(self, type_name: str) -> None:
        """Unregister a type and all its instances.

        Args:
            type_name: Type to unregister.

        Raises:
            KeyError: If the type is not registered.
            ValueError: If the type has children that must be removed first.
        """
        type_name = type_name.lower()
        if type_name not in self._types:
            raise KeyError(f"Type '{type_name}' is not registered.")

        children = self._hierarchy.get_children(type_name)
        if children:
            raise ValueError(
                f"Cannot unregister '{type_name}': it has child type(s): "
                f"{', '.join(sorted(children))}. Remove children first."
            )

        del self._types[type_name]
        self._objects.pop(type_name, None)
        self._type_metadata.pop(type_name, None)
        self._hierarchy.remove_type(type_name)

    def list_types(self) -> list[dict[str, Any]]:
        """List all registered types with metadata.

        Returns:
            List of dicts with type metadata sorted by type name.
        """
        return [
            self._type_metadata[name].to_dict()
            for name in sorted(self._types.keys())
        ]

    def has_type(self, type_name: str) -> bool:
        """Check if a type is registered."""
        return type_name.lower() in self._types

    def get_type_metadata(self, type_name: str) -> ObjectMetadata | None:
        """Get metadata for a registered type, or None."""
        return self._type_metadata.get(type_name.lower())

    def get_type_class(self, type_name: str) -> type[Any] | None:
        """Get the Python class for a registered type, or None."""
        return self._types.get(type_name.lower())

    # ------------------------------------------------------------------
    # Object Registration & Discovery
    # ------------------------------------------------------------------

    def register_object(
        self,
        type_name: str,
        object_id: str,
        obj: Any,
    ) -> None:
        """Register an object instance under a given type.

        The object is indexed by its id for fast lookup. If a
        ProtocolComplianceChecker is attached, the object is verified
        on registration.

        Args:
            type_name: Registered type name.
            object_id: Unique identifier for the object.
            obj: The object instance.

        Raises:
            KeyError: If the type is not registered.
            ValueError: If the type is abstract.
            ValueError: If an object with the same id already exists
                        under this type.
        """
        type_name = type_name.lower()
        if type_name not in self._types:
            raise KeyError(
                f"Cannot register object: type '{type_name}' is not registered."
            )
        if self._hierarchy.is_abstract(type_name):
            raise ValueError(
                f"Cannot register object: type '{type_name}' is abstract."
            )
        if object_id in self._objects.get(type_name, {}):
            raise ValueError(
                f"Object '{object_id}' is already registered under type '{type_name}'."
            )

        self._objects.setdefault(type_name, {})[object_id] = obj

    def unregister_object(self, type_name: str, object_id: str) -> None:
        """Remove an object from the registry.

        Args:
            type_name: Type the object is registered under.
            object_id: Object identifier.

        Raises:
            KeyError: If the type or object is not found.
        """
        type_name = type_name.lower()
        if type_name not in self._objects:
            raise KeyError(f"Type '{type_name}' is not registered.")
        if object_id not in self._objects[type_name]:
            raise KeyError(
                f"Object '{object_id}' is not registered under type '{type_name}'."
            )
        del self._objects[type_name][object_id]

    def find_by_type(self, type_name: str) -> list[Any]:
        """Find all objects of a given type.

        Includes objects of descendant (child) types.

        Args:
            type_name: Type name to search for.

        Returns:
            List of objects matching the type or its descendants.
        """
        type_name = type_name.lower()
        results: list[Any] = []

        # Direct matches
        results.extend(self._objects.get(type_name, {}).values())

        # Descendant matches
        for descendant in self._hierarchy.get_descendants(type_name):
            results.extend(self._objects.get(descendant, {}).values())

        return results

    def find_by_id(self, object_id: str) -> Any | None:
        """Find an object by its id across all registered types.

        Returns the first match, or None if not found.
        """
        for type_objects in self._objects.values():
            if object_id in type_objects:
                return type_objects[object_id]
        return None

    def find_by_type_and_id(self, type_name: str, object_id: str) -> Any | None:
        """Find an object by type and id.

        Args:
            type_name: Type name.
            object_id: Object identifier.

        Returns:
            The object or None.
        """
        return self._objects.get(type_name.lower(), {}).get(object_id)

    def find_by_field(
        self,
        field: str,
        value: Any,
        type_name: str | None = None,
    ) -> list[Any]:
        """Find objects where a named field equals a value.

        Uses getattr-style access. Objects without the field are
        silently skipped.

        Args:
            field: Attribute name to inspect.
            value: Expected value (compared with ==).
            type_name: Optional type filter. If omitted, searches all types.

        Returns:
            List of matching objects.
        """
        results: list[Any] = []
        target_types = (
            [type_name.lower()]
            if type_name
            else list(self._objects.keys())
        )

        for tn in target_types:
            for obj in self._objects.get(tn, {}).values():
                try:
                    if hasattr(obj, field) and getattr(obj, field) == value:
                        results.append(obj)
                except Exception:
                    pass

        return results

    def count_objects(self, type_name: str | None = None) -> int:
        """Count registered objects, optionally filtered by type."""
        if type_name:
            return len(self._objects.get(type_name.lower(), {}))
        return sum(len(obs) for obs in self._objects.values())

    # ------------------------------------------------------------------
    # Type Hierarchy Queries
    # ------------------------------------------------------------------

    def get_parent_type(self, type_name: str) -> str | None:
        """Get the parent type name, or None."""
        return self._hierarchy.get_parent(type_name.lower())

    def get_child_types(self, type_name: str) -> set[str]:
        """Get direct child type names."""
        return self._hierarchy.get_children(type_name.lower())

    def get_descendant_types(self, type_name: str) -> set[str]:
        """Get all descendant type names."""
        return self._hierarchy.get_descendants(type_name.lower())

    def is_abstract_type(self, type_name: str) -> bool:
        """Check if a type is abstract."""
        return self._hierarchy.is_abstract(type_name.lower())

    def is_subtype(self, type_name: str, potential_parent: str) -> bool:
        """Check if type_name is a descendant of potential_parent."""
        return self._hierarchy.is_subtype_of(
            type_name.lower(), potential_parent.lower()
        )

    # ------------------------------------------------------------------
    # Protocol Compliance
    # ------------------------------------------------------------------

    def check_protocol_compliance(self, obj: Any) -> ComplianceReport:
        """Check if an object implements all 15 protocol sections.

        If a ProtocolComplianceChecker is attached, delegates to it.
        Otherwise, performs a basic check by looking for expected
        attributes.

        Args:
            obj: The object to verify.

        Returns:
            ComplianceReport with per-section results.
        """
        if self._compliance_checker:
            return self._compliance_checker.full_compliance_check(obj)

        # Fallback: attribute-based check for the 15 sections
        section_attrs: dict[str, list[str]] = {
            "identity": ["object_id", "identity_type"],
            "metadata": ["created_at", "updated_at", "created_by"],
            "relationships": ["relationships"],
            "timeline": ["events", "add_event", "get_events"],
            "lifecycle": ["current_stage", "valid_transitions", "transition"],
            "status": ["status", "is_active"],
            "ownership": ["owner_id", "owner_type", "transfer"],
            "permissions": ["acl", "check_permission", "grant", "revoke"],
            "evidence": ["evidence_ids", "add_evidence", "get_evidence_chain"],
            "ai_context": ["ai_summary", "get_ai_context"],
            "search": ["search"],
            "audit": ["audit_log", "log_action", "verify_integrity"],
            "actions": ["available_actions", "execute_action", "get_available_actions"],
            "versioning": ["version", "version_history", "get_version"],
        }

        checks: dict[str, bool] = {}
        failures: list[str] = []

        for section, attrs in section_attrs.items():
            passed = all(hasattr(obj, attr) for attr in attrs)
            checks[section] = passed
            if not passed:
                failures.append(section)

        detail = (
            "All 15 protocol sections are compliant."
            if not failures
            else f"Non-compliant sections: {', '.join(failures)}."
        )

        return ComplianceReport(
            compliant=len(failures) == 0,
            checks=checks,
            failures=failures,
            details=detail,
        )

    # ------------------------------------------------------------------
    # Version Compatibility
    # ------------------------------------------------------------------

    def check_version_compatibility(
        self,
        type_name: str,
        version: str,
    ) -> bool:
        """Check if a version is compatible with the current runtime.

        Compares the given version against the type's
        min_compatible_version using semantic versioning rules.

        Args:
            type_name: Registered type name.
            version: Version string to check (e.g. '1.2.3').

        Returns:
            True if compatible, False if not or if type is unknown.
        """
        meta = self._type_metadata.get(type_name.lower())
        if meta is None:
            return False
        return self._version_gte(version, meta.min_compatible_version)

    @staticmethod
    def _version_gte(v1: str, v2: str) -> bool:
        """Semver: return True if v1 >= v2, ignoring pre-release labels."""

        def _parse(v: str) -> tuple:
            parts = v.split(".")[:3]
            while len(parts) < 3:
                parts.append("0")
            return tuple(int(p) if p.isdigit() else 0 for p in parts)

        return _parse(v1) >= _parse(v2)

    # ------------------------------------------------------------------
    # Compliance Checker Attachment
    # ------------------------------------------------------------------

    def set_compliance_checker(
        self, checker: ProtocolComplianceChecker
    ) -> None:
        """Attach a ProtocolComplianceChecker for full protocol verification."""
        self._compliance_checker = checker

    def get_compliance_checker(self) -> ProtocolComplianceChecker | None:
        """Get the attached compliance checker, or None."""
        return self._compliance_checker

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, object_id: str) -> dict[str, Any] | None:
        """Retrieve metadata about a registered object.

        Returns a dict with type_name, registered_at, and protocol_status.
        Returns None if the object is not found.
        """
        for type_name, objects in self._objects.items():
            if object_id in objects:
                obj = objects[object_id]
                compliance = self.check_protocol_compliance(obj)
                return {
                    "type_name": type_name,
                    "object_id": object_id,
                    "compliant": compliance.compliant,
                    "compliance_checks": dict(compliance.checks),
                }
        return None

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def diagnostics(self) -> dict[str, Any]:
        """Return detailed registry state for debugging."""
        return {
            "type_count": len(self._types),
            "object_count": self.count_objects(),
            "types": {
                name: {
                    "version": self._type_metadata[name].version,
                    "abstract": self._hierarchy.is_abstract(name),
                    "parent": self._hierarchy.get_parent(name),
                    "object_count": len(self._objects.get(name, {})),
                }
                for name in sorted(self._types.keys())
            },
            "hierarchy": self._hierarchy.to_dict(),
        }


# =========================================================================
# Protocol Compliance Checker
# =========================================================================


class ProtocolComplianceChecker:
    """Verifies that an object implements all 15 mandatory sections of the
    Universal Object Protocol.

    Each check_* method inspects a specific protocol section by looking
    for required attributes and methods on the object. The
    full_compliance_check() method runs all 15 checks and returns a
    ComplianceReport.

    Usage:
        checker = ProtocolComplianceChecker()
        report = checker.full_compliance_check(my_object)
        if report.compliant:
            print("Object implements the full Universal Object Protocol!")
        else:
            print(f"Failed sections: {report.failures}")
    """

    # ------------------------------------------------------------------
    # Per-section checks
    # ------------------------------------------------------------------

    def check_identity(self, obj: Any) -> bool:
        """Check the Identity section: object_id, external_ids, identity_type."""
        return (
            hasattr(obj, "object_id")
            and hasattr(obj, "external_ids")
            and hasattr(obj, "identity_type")
        )

    def check_metadata(self, obj: Any) -> bool:
        """Check the Metadata section: created_at, updated_at, created_by, source."""
        return (
            hasattr(obj, "created_at")
            and hasattr(obj, "updated_at")
            and hasattr(obj, "created_by")
            and hasattr(obj, "source")
        )

    def check_relationships(self, obj: Any) -> bool:
        """Check the Relationships section: relationships list, add/remove/get."""
        return (
            hasattr(obj, "relationships")
            and hasattr(obj, "add_relationship")
            and hasattr(obj, "remove_relationship")
            and hasattr(obj, "get_relationships")
        )

    def check_timeline(self, obj: Any) -> bool:
        """Check the Timeline section: add_event, get_events, get_latest_events."""
        return (
            hasattr(obj, "add_event")
            and hasattr(obj, "get_events")
            and hasattr(obj, "get_latest_events")
        )

    def check_lifecycle(self, obj: Any) -> bool:
        """Check the Lifecycle section: current_stage, valid_transitions, transition."""
        return (
            hasattr(obj, "current_stage")
            and hasattr(obj, "valid_transitions")
            and hasattr(obj, "transition")
        )

    def check_status(self, obj: Any) -> bool:
        """Check the Status section: status, is_active."""
        return (
            hasattr(obj, "status")
            and hasattr(obj, "is_active")
        )

    def check_ownership(self, obj: Any) -> bool:
        """Check the Ownership section: owner_id, owner_type, transfer."""
        return (
            hasattr(obj, "owner_id")
            and hasattr(obj, "owner_type")
            and hasattr(obj, "transfer")
        )

    def check_permissions(self, obj: Any) -> bool:
        """Check the Permissions section: acl, check_permission, grant, revoke."""
        return (
            hasattr(obj, "acl")
            and hasattr(obj, "check_permission")
            and hasattr(obj, "grant")
            and hasattr(obj, "revoke")
        )

    def check_evidence(self, obj: Any) -> bool:
        """Check the Evidence section: get_evidence, add_evidence, get_evidence_chain."""
        return (
            hasattr(obj, "add_evidence")
            and hasattr(obj, "get_evidence")
            and hasattr(obj, "get_evidence_chain")
        )

    def check_ai_context(self, obj: Any) -> bool:
        """Check the AI Context section: ai_summary, get_ai_context."""
        return (
            hasattr(obj, "ai_summary")
            and hasattr(obj, "get_ai_context")
        )

    def check_search(self, obj: Any) -> bool:
        """Check the Search section: search method."""
        return hasattr(obj, "search")

    def check_audit(self, obj: Any) -> bool:
        """Check the Audit section: get_audit_log, log_action, verify_integrity."""
        return (
            hasattr(obj, "get_audit_log")
            and hasattr(obj, "log_action")
            and hasattr(obj, "verify_integrity")
        )

    def check_actions(self, obj: Any) -> bool:
        """Check the Actions section: available_actions, execute_action, get_available_actions."""
        return (
            hasattr(obj, "available_actions")
            and hasattr(obj, "execute_action")
            and hasattr(obj, "get_available_actions")
        )

    def check_versioning(self, obj: Any) -> bool:
        """Check the Versioning section: version, version_history, get_version."""
        return (
            hasattr(obj, "version")
            and hasattr(obj, "version_history")
            and hasattr(obj, "get_version")
        )

    # ------------------------------------------------------------------
    # Aggregate check
    # ------------------------------------------------------------------

    def full_compliance_check(
        self,
        obj: Any,
        verbose: bool = False,
    ) -> ComplianceReport:
        """Run all 15 protocol checks and return a ComplianceReport.

        Args:
            obj: The object to verify.
            verbose: If True, include per-check detail messages in details.

        Returns:
            ComplianceReport with per-section results.
        """
        checkers: dict[str, Callable[[Any], bool]] = {
            "identity": self.check_identity,
            "metadata": self.check_metadata,
            "relationships": self.check_relationships,
            "timeline": self.check_timeline,
            "lifecycle": self.check_lifecycle,
            "status": self.check_status,
            "ownership": self.check_ownership,
            "permissions": self.check_permissions,
            "evidence": self.check_evidence,
            "ai_context": self.check_ai_context,
            "search": self.check_search,
            "audit": self.check_audit,
            "actions": self.check_actions,
            "versioning": self.check_versioning,
        }

        checks: dict[str, bool] = {}
        failures: list[str] = []

        for section, checker in checkers.items():
            try:
                passed = checker(obj)
            except Exception:
                passed = False

            checks[section] = passed
            if not passed:
                failures.append(section)

        compliant = len(failures) == 0

        if verbose:
            lines: list[str] = []
            for section in sorted(checks.keys()):
                status = "PASS" if checks[section] else "FAIL"
                lines.append(f"  [{status}] {section}")
            detail = (
                "All 15 protocol sections are compliant."
                if compliant
                else f"{len(failures)} non-compliant section(s):\n"
                + "\n".join(lines)
            )
        else:
            detail = (
                "All 15 protocol sections are compliant."
                if compliant
                else f"Non-compliant sections: {', '.join(failures)}."
            )

        return ComplianceReport(
            compliant=compliant,
            checks=checks,
            failures=failures,
            details=detail,
        )


# =========================================================================
# Default checker singleton
# =========================================================================

_DEFAULT_CHECKER: ProtocolComplianceChecker | None = None


def get_compliance_checker() -> ProtocolComplianceChecker:
    """Get or create the default ProtocolComplianceChecker singleton."""
    global _DEFAULT_CHECKER
    if _DEFAULT_CHECKER is None:
        _DEFAULT_CHECKER = ProtocolComplianceChecker()
    return _DEFAULT_CHECKER


def reset_compliance_checker() -> None:
    """Reset the default checker singleton (for testing)."""
    global _DEFAULT_CHECKER
    _DEFAULT_CHECKER = None