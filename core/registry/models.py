"""
SHUNYA Object Registry — Domain Models

Defines the canonical data types for the object registry:
ComplianceReport, ObjectMetadata, and the 15 protocol sections
that every Universal Object must implement.

The Universal Object Protocol defines 15 mandatory sections that
every managed object in SHUNYA must satisfy:
  Identity, Metadata, Relationships, Timeline, Lifecycle, Status,
  Ownership, Permissions, Evidence, AI Context, Search, Audit,
  Actions, Versioning, and Search.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

# =========================================================================
# Enums
# =========================================================================


class ProtocolSection(StrEnum):
    """Each of the 15 mandatory sections of the Universal Object Protocol."""

    IDENTITY = "identity"
    METADATA = "metadata"
    RELATIONSHIPS = "relationships"
    TIMELINE = "timeline"
    LIFECYCLE = "lifecycle"
    STATUS = "status"
    OWNERSHIP = "ownership"
    PERMISSIONS = "permissions"
    EVIDENCE = "evidence"
    AI_CONTEXT = "ai_context"
    SEARCH = "search"
    AUDIT = "audit"
    ACTIONS = "actions"
    VERSIONING = "versioning"

    @classmethod
    def all_sections(cls) -> list[ProtocolSection]:
        """Return all 15 protocol sections."""
        return list(cls)


class ObjectStatus(StrEnum):
    """Lifecycle status of a managed object."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    PENDING = "pending"


# =========================================================================
# Object Metadata
# =========================================================================


@dataclass
class ObjectMetadata:
    """Metadata associated with a registered object type."""

    type_name: str
    """Name of the object type (e.g. 'task', 'decision', 'prediction')."""

    version: str = "1.0.0"
    """Current version of this type."""

    description: str = ""
    """Human-readable description of the type."""

    parent_type: str | None = None
    """Optional parent type for type hierarchy."""

    is_abstract: bool = False
    """If True, instances of this type cannot be created directly."""

    created_at: str = ""
    """ISO-8601 timestamp of when this type was registered."""

    min_compatible_version: str = "1.0.0"
    """Minimum version that is backward-compatible with the current runtime."""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "type_name": self.type_name,
            "version": self.version,
            "description": self.description,
            "parent_type": self.parent_type,
            "is_abstract": self.is_abstract,
            "created_at": self.created_at,
            "min_compatible_version": self.min_compatible_version,
        }


# =========================================================================
# Compliance Report
# =========================================================================


@dataclass
class ComplianceReport:
    """Result of a full protocol compliance check on an object.

    Reports which of the 15 mandatory sections pass or fail, with
    a summary of failures and an overall compliant flag.
    """

    compliant: bool
    """True when every protocol section passes its check."""

    checks: dict[str, bool] = field(default_factory=dict)
    """Per-section compliance: section name → passed (True/False)."""

    failures: list[str] = field(default_factory=list)
    """Names of sections that failed compliance."""

    details: str = ""
    """Human-readable summary of the compliance findings."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "compliant": self.compliant,
            "checks": dict(self.checks),
            "failures": list(self.failures),
            "details": self.details,
        }

    @classmethod
    def passed(cls) -> ComplianceReport:
        """Create a fully compliant report (all checks pass)."""
        sections = [s.value for s in ProtocolSection.all_sections()]
        return cls(
            compliant=True,
            checks={s: True for s in sections},
            failures=[],
            details="All 15 protocol sections are compliant.",
        )

    @classmethod
    def failed(cls, failures: dict[str, bool], detail: str = "") -> ComplianceReport:
        """Create a non-compliant report from per-section results.

        Args:
            failures: Mapping of section name → passed (False for failed sections).
            detail: Optional summary description of what failed.
        """
        fails = [s for s, p in failures.items() if not p]
        return cls(
            compliant=False,
            checks=failures,
            failures=fails,
            details=detail or f"Non-compliant sections: {', '.join(fails)}",
        )