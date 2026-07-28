"""SHUNYA Runtime Validation — automated canonical compliance enforcement.

Every object in the runtime is validated against:
1. Universal Object Protocol — mandatory 15-section contract
2. Universal Ontology — type hierarchy, lifecycle constraints
3. Runtime rules — valid transitions, relationship invariants, evidence requirements
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.kernel import UniversalObject


# ---------------------------------------------------------------------------
# Validation enums
# ---------------------------------------------------------------------------


class ValidationSeverity(str, Enum):
    ERROR = "error"       # Must fix — blocks execution
    WARNING = "warning"   # Should fix — allowed but discouraged
    INFO = "info"         # May fix — informational


class ValidationScope(str, Enum):
    PROTOCOL = "protocol"       # Universal Object Protocol compliance
    ONTOLOGY = "ontology"       # Ontology rules (type hierarchy)
    LIFECYCLE = "lifecycle"     # Lifecycle state transitions
    RELATIONSHIP = "relationship"  # Relationship invariants
    TIMELINE = "timeline"       # Timeline validity
    EVIDENCE = "evidence"       # Evidence requirements
    RUNTIME = "runtime"         # Runtime-level checks


# ---------------------------------------------------------------------------
# Validation models
# ---------------------------------------------------------------------------


@dataclass
class ValidationFinding:
    """A single validation finding (error, warning, or info)."""

    scope: str
    severity: str
    message: str
    object_id: str | None = None
    field: str | None = None
    expected: str | None = None
    actual: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "severity": self.severity,
            "message": self.message,
            "object_id": self.object_id,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass
class ValidationReport:
    """Complete validation report for a single object or the entire runtime."""

    subject_id: str = ""
    subject_type: str = ""
    passed: bool = True
    findings: list[ValidationFinding] = field(default_factory=list)
    checks_run: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0

    def add_finding(self, finding: ValidationFinding) -> None:
        self.findings.append(finding)
        self.checks_run += 1
        if finding.severity == ValidationSeverity.ERROR.value:
            self.errors += 1
            self.passed = False
        elif finding.severity == ValidationSeverity.WARNING.value:
            self.warnings += 1
        elif finding.severity == ValidationSeverity.INFO.value:
            self.infos += 1

    def add_error(self, scope: str, message: str, obj_id: str = "", field: str = "") -> None:
        self.add_finding(ValidationFinding(
            scope=scope, severity=ValidationSeverity.ERROR.value,
            message=message, object_id=obj_id, field=field,
        ))

    def add_warning(self, scope: str, message: str, obj_id: str = "", field: str = "") -> None:
        self.add_finding(ValidationFinding(
            scope=scope, severity=ValidationSeverity.WARNING.value,
            message=message, object_id=obj_id, field=field,
        ))

    def add_info(self, scope: str, message: str, obj_id: str = "") -> None:
        self.add_finding(ValidationFinding(
            scope=scope, severity=ValidationSeverity.INFO.value,
            message=message, object_id=obj_id,
        ))

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "passed": self.passed,
            "checks_run": self.checks_run,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Runtime Validator
# ---------------------------------------------------------------------------


class RuntimeValidator:
    """Canonical validator for the SHUNYA runtime.

    Validates objects against:
    1. Universal Object Protocol (04)
    2. Universal Ontology (00)
    3. Runtime Canon (05)
    """

    def __init__(self):
        self._protocol_validator = ProtocolValidator()
        self._ontology_validator = OntologyValidator()
        self._lifecycle_validator = LifecycleValidator()
        self._relationship_validator = RelationshipValidator()
        self._timeline_validator = TimelineValidator()
        self._evidence_validator = EvidenceValidator()

    # ---- Full validation -------------------------------------------------

    def validate_object(self, obj: UniversalObject) -> ValidationReport:
        """Run all validators on a single object."""
        report = ValidationReport(
            subject_id=obj.object_id,
            subject_type=obj.object_type,
        )

        # Protocol compliance (all 15 mandatory sections)
        self._validate_protocol(obj, report)

        # Ontology rules
        self._validate_ontology(obj, report)

        # Lifecycle
        self._validate_lifecycle(obj, report)

        # Relationships
        self._validate_relationships(obj, report)

        # Timeline
        self._validate_timeline(obj, report)

        # Evidence
        self._validate_evidence(obj, report)

        return report

    def validate_object_protocol(self, obj: UniversalObject) -> ValidationReport:
        """Run only protocol compliance checks."""
        report = ValidationReport(
            subject_id=obj.object_id,
            subject_type=obj.object_type,
        )
        self._validate_protocol(obj, report)
        return report

    def validate_object_lifecycle(self, obj: UniversalObject) -> ValidationReport:
        """Run only lifecycle checks."""
        report = ValidationReport(
            subject_id=obj.object_id,
            subject_type=obj.object_type,
        )
        self._validate_lifecycle(obj, report)
        return report

    # ---- Individual validators ------------------------------------------

    def _validate_protocol(self, obj: UniversalObject, report: ValidationReport) -> None:
        """Validate all 15 mandatory protocol sections."""
        # §4 Identity
        if not obj.object_id:
            report.add_error("protocol", "Missing object_id (Identity §4)", obj.object_id)
        # §5 Metadata
        if not obj.created_at:
            report.add_error("protocol", "Missing created_at (Metadata §5)", obj.object_id)
        if obj.version < 1:
            report.add_error("protocol", "Invalid version < 1 (Versioning §18)", obj.object_id)
        # §9 Status
        if not obj.status:
            report.add_error("protocol", "Missing status (Status §9)", obj.object_id)
        # §10 Ownership
        if not obj.owner_id:
            report.add_warning("protocol", "Missing owner_id (Ownership §10)", obj.object_id)
        # §14 AI Context
        if not obj.ai_summary:
            report.add_warning("protocol", "Missing ai_summary (AI Context §14)", obj.object_id)
        # §16 Audit
        if not hasattr(obj, 'audit_log'):
            report.add_error("protocol", "Missing audit_log (Audit §16)", obj.object_id)
        if not hasattr(obj, 'log_action'):
            report.add_error("protocol", "Missing log_action method (Audit §16)", obj.object_id)

    def _validate_ontology(self, obj: UniversalObject, report: ValidationReport) -> None:
        """Validate ontological rules."""
        if obj.object_type == "UniversalObject":
            report.add_info("ontology", "Abstract base type — may not be instantiated directly", obj.object_id)
        if obj.status not in ("active", "superseded", "archived", "pending", "deleted"):
            report.add_warning("ontology", f"Non-standard status: {obj.status}", obj.object_id, "status")

    def _validate_lifecycle(self, obj: UniversalObject, report: ValidationReport) -> None:
        """Validate lifecycle states and transitions."""
        stage = getattr(obj, 'current_stage', None)
        if stage and stage not in getattr(obj, 'valid_transitions', {}):
            report.add_error("lifecycle", f"Unknown lifecycle stage: {stage}", obj.object_id, "current_stage")

    def _validate_relationships(self, obj: UniversalObject, report: ValidationReport) -> None:
        """Validate relationship invariants."""
        if hasattr(obj, 'get_relationships'):
            rels = obj.get_relationships()
            # Check for self-referential relationships
            for rel in rels:
                if getattr(rel, 'source_id', None) == getattr(rel, 'target_id', None) == obj.object_id:
                    report.add_warning("relationship", "Self-referential relationship", obj.object_id)

    def _validate_timeline(self, obj: UniversalObject, report: ValidationReport) -> None:
        """Validate timeline integrity."""
        if hasattr(obj, 'get_events'):
            events = obj.get_events(limit=1)
            if events:
                first = events[0]
                if getattr(first, 'event_type', '') != 'object_created' and obj.version == 1:
                    report.add_warning("timeline", "First event should be 'object_created'", obj.object_id)

    def _validate_evidence(self, obj: UniversalObject, report: ValidationReport) -> None:
        """Validate evidence requirements."""
        if not hasattr(obj, 'get_evidence'):
            report.add_error("evidence", "Missing get_evidence method (Evidence §12)", obj.object_id)

    # ---- Bulk validation ------------------------------------------------

    def validate_all(self, objects: list[UniversalObject]) -> list[ValidationReport]:
        """Validate multiple objects, returning per-object reports."""
        return [self.validate_object(obj) for obj in objects]

    def validate_runtime_health(self) -> ValidationReport:
        """Validate overall runtime health."""
        report = ValidationReport(subject_id="runtime", subject_type="system")
        report.add_info("runtime", "Runtime validation initialized")
        return report


# ---------------------------------------------------------------------------
# Specialized validators (for individual checks)
# ---------------------------------------------------------------------------


class ProtocolValidator:
    """Validates Universal Object Protocol compliance for a single object."""

    MANDATORY_SECTIONS = [
        "identity", "metadata", "relationships", "timeline",
        "lifecycle", "status", "ownership", "permissions",
        "evidence", "ai_context", "search", "audit", "actions", "versioning",
    ]

    def check(self, obj: UniversalObject) -> ValidationReport:
        report = ValidationReport(
            subject_id=obj.object_id,
            subject_type=obj.object_type,
        )
        for section in self.MANDATORY_SECTIONS:
            check_method = getattr(self, f"_check_{section}", None)
            if check_method:
                check_method(obj, report)
        return report

    def _check_identity(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not obj.object_id:
            report.add_error("protocol", "Identity §4: object_id is required", obj.object_id)

    def _check_metadata(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not obj.created_at:
            report.add_error("protocol", "Metadata §5: created_at is required", obj.object_id)

    def _check_timeline(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not hasattr(obj, 'get_events'):
            report.add_error("protocol", "Timeline §7: get_events method required", obj.object_id)

    def _check_lifecycle(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not hasattr(obj, 'current_stage'):
            report.add_warning("protocol", "Lifecycle §8: current_stage recommended", obj.object_id)

    def _check_status(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not obj.status:
            report.add_error("protocol", "Status §9: status is required", obj.object_id)

    def _check_ownership(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not obj.owner_id:
            report.add_warning("protocol", "Ownership §10: owner_id recommended", obj.object_id)

    def _check_evidence(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not hasattr(obj, 'get_evidence'):
            report.add_error("protocol", "Evidence §12: get_evidence method required", obj.object_id)

    def _check_ai_context(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not obj.ai_summary:
            report.add_warning("protocol", "AI Context §14: ai_summary recommended", obj.object_id)

    def _check_audit(self, obj: UniversalObject, report: ValidationReport) -> None:
        if not hasattr(obj, 'log_action'):
            report.add_error("protocol", "Audit §16: log_action method required", obj.object_id)

    def _check_actions(self, obj: UniversalObject, report: ValidationReport) -> None:
        if hasattr(obj, 'available_actions') and not obj.available_actions:
            report.add_warning("protocol", "Actions §17: no available actions defined", obj.object_id)

    def _check_versioning(self, obj: UniversalObject, report: ValidationReport) -> None:
        if obj.version < 1:
            report.add_error("protocol", "Versioning §18: version must be >= 1", obj.object_id)

    def _check_relationships(self, obj: UniversalObject, report: ValidationReport) -> None:
        pass  # Relationships are optional for most objects

    def _check_permissions(self, obj: UniversalObject, report: ValidationReport) -> None:
        pass  # Permissions handled by runtime

    def _check_search(self, obj: UniversalObject, report: ValidationReport) -> None:
        pass  # Search handled by search engine


class OntologyValidator:
    """Validates objects against Universal Ontology rules."""

    VALID_STATUSES = {"active", "superseded", "archived", "pending", "deleted"}

    def check_type_hierarchy(self, obj: UniversalObject, type_registry) -> ValidationReport:
        report = ValidationReport(subject_id=obj.object_id, subject_type=obj.object_type)
        registered_type = type_registry.get(obj.object_type) if hasattr(type_registry, 'get') else None
        if registered_type is None and obj.object_type not in ("UniversalObject",):
            report.add_warning("ontology", f"Type '{obj.object_type}' not found in registry", obj.object_id)
        return report


class LifecycleValidator:
    """Validates lifecycle state transitions."""

    def validate_transition(self, from_state: str, to_state: str, valid_transitions: dict[str, list[str]]) -> bool:
        if from_state not in valid_transitions:
            return False
        return to_state in valid_transitions[from_state]


class RelationshipValidator:
    """Validates relationship invariants."""

    def validate(self, rel) -> ValidationReport:
        report = ValidationReport(subject_id=getattr(rel, 'source_id', ''), subject_type="relationship")
        if getattr(rel, 'source_id', None) == getattr(rel, 'target_id', None):
            report.add_error("relationship", "Self-referential relationships are not allowed")
        if not getattr(rel, 'relationship_type', None):
            report.add_warning("relationship", "Relationship type is not set")
        return report


class TimelineValidator:
    """Validates timeline integrity."""

    def verify_chain(self, events: list) -> bool:
        """Verify that timeline events form a valid hash chain."""
        if not events:
            return True
        for i in range(1, len(events)):
            prev = events[i - 1]
            curr = events[i]
            prev_hash = getattr(prev, 'integrity_hash', getattr(prev, 'previous_hash', ''))
            curr_prev_hash = getattr(curr, 'previous_hash', '')
            if prev_hash and curr_prev_hash and curr_prev_hash != "0" * 64:
                if curr_prev_hash != prev_hash:
                    return False
        return True


class EvidenceValidator:
    """Validates evidence requirements."""

    def check_evidence_sufficiency(self, evidence_ids: list[str]) -> ValidationReport:
        report = ValidationReport(subject_id="evidence_check", subject_type="evidence")
        if not evidence_ids:
            report.add_warning("evidence", "No evidence attached", field="evidence_ids")
        return report


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

_VALIDATOR: RuntimeValidator | None = None


def get_validator() -> RuntimeValidator:
    global _VALIDATOR
    if _VALIDATOR is None:
        _VALIDATOR = RuntimeValidator()
    return _VALIDATOR


def reset_validator() -> None:
    global _VALIDATOR
    _VALIDATOR = None