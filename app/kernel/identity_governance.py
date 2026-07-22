"""SHUNYA Kernel — Identity Governance.

Implements identity governance operations defined in:
    UNIVERSAL_ONTOLOGY.md §3 — Identity
    UNIVERSAL_ONTOLOGY.md §3.5 — Identity merge, split, deletion

Governance rules:
    - Identities are permanent (never truly deleted, only retired)
    - Merge preserves evidence (both identities' evidence is retained)
    - Split partitions evidence (evidence is distributed across new identities)
    - Retired identities are never reused
    - All governance operations are auditable
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.kernel.identity import (
    SHUNYAIdentity, IdentityStore, AuthenticationMethod,
    get_identity_store,
)
from app.kernel.object import EvidenceRef


# ---------------------------------------------------------------------------
# Audit entry — every governance operation produces one
# ---------------------------------------------------------------------------

class AuditAction(str):
    """Canonical governance audit actions."""
    MERGE = "merge"
    SPLIT = "split"
    RETIRE = "retire"
    RESTORE = "restore"
    LINK = "link"
    UNLINK = "unlink"
    RENAME = "rename"


@dataclass
class IdentityAuditEntry:
    """A single audit event recording a governance operation.

    Attributes:
        audit_id: Unique audit event identifier
        action: The governance action performed
        identity_id: The primary identity affected
        secondary_id: Secondary identity (for merge/split), or None
        reason: Why the action was taken
        actor: Who or what performed the action
        details: Additional operation-specific data
        timestamp: When the action occurred
    """
    audit_id: str
    action: str
    identity_id: str
    secondary_id: Optional[str] = None
    reason: str = ""
    actor: str = "system"
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "action": self.action,
            "identity_id": self.identity_id,
            "secondary_id": self.secondary_id,
            "reason": self.reason,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Merge / Split plans — preview before executing
# ---------------------------------------------------------------------------

@dataclass
class IdentityMergePlan:
    """Preview of an identity merge before execution.

    Attributes:
        source_id: Identity that will be merged INTO target (then retired)
        target_id: Identity that will absorb the source
        source_display_name: Display name of source identity
        target_display_name: Display name of target identity
        auth_methods_to_transfer: Auth methods that will move from source to target
        evidence_count_source: Number of evidence refs on source
        evidence_count_target: Number of evidence refs on target (after merge)
        potential_conflicts: Any conflicts detected that need resolution
    """
    source_id: str
    target_id: str
    source_display_name: str = ""
    target_display_name: str = ""
    auth_methods_to_transfer: int = 0
    evidence_count_source: int = 0
    evidence_count_target: int = 0
    potential_conflicts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_display_name": self.source_display_name,
            "target_display_name": self.target_display_name,
            "auth_methods_to_transfer": self.auth_methods_to_transfer,
            "evidence_count_source": self.evidence_count_source,
            "evidence_count_target": self.evidence_count_target,
            "potential_conflicts": self.potential_conflicts,
        }


@dataclass
class IdentitySplitPartition:
    """A single partition in an identity split.

    Attributes:
        auth_methods: Auth methods assigned to this partition
        evidence: Evidence refs assigned to this partition
        new_display_name: Display name for the new identity
    """
    auth_methods: List[AuthenticationMethod] = field(default_factory=list)
    evidence: List[EvidenceRef] = field(default_factory=list)
    new_display_name: str = ""


@dataclass
class IdentitySplitPlan:
    """Preview of an identity split before execution.

    Attributes:
        source_id: Identity that will be split
        partitions: List of planned partitions
        unassigned_auth_methods: Auth methods not yet assigned to any partition
        unassigned_evidence: Evidence refs not yet assigned to any partition
    """
    source_id: str
    partitions: List[IdentitySplitPartition] = field(default_factory=list)
    unassigned_auth_methods: int = 0
    unassigned_evidence: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "partition_count": len(self.partitions),
            "unassigned_auth_methods": self.unassigned_auth_methods,
            "unassigned_evidence": self.unassigned_evidence,
        }


# ---------------------------------------------------------------------------
# Identity Governance
# ---------------------------------------------------------------------------

class IdentityGovernance:
    """Governance operations for SHUNYA Identities.

    Constitutional invariants enforced:
        O-01: Identity never changes (identity_id is immutable)
        O-04: Context is always traceable to its source (audit trail)
        I-01: Identities are permanent (never truly deleted, only retired)
        I-02: Merge preserves evidence (both sources retained in audit)
        I-03: Split partitions evidence (each partition inherits relevant evidence)
        I-04: Retired identities are never reused
    """

    def __init__(self, store: Optional[IdentityStore] = None):
        self._store = store or get_identity_store()
        self._audit_log: List[IdentityAuditEntry] = []
        self._audit_counter: int = 0

    @property
    def audit_log(self) -> List[IdentityAuditEntry]:
        """Full immutable audit log of all governance operations."""
        return list(self._audit_log)

    # ---- Merge ---------------------------------------------------------

    def plan_merge(
        self,
        source_id: str,
        target_id: str,
    ) -> IdentityMergePlan:
        """Preview a merge operation before executing it.

        Args:
            source_id: Identity to merge INTO target (then retired)
            target_id: Identity that will absorb the source

        Returns:
            IdentityMergePlan with conflict analysis

        Raises:
            ValueError: If either identity does not exist or is retired
        """
        source = self._store.get(source_id)
        target = self._store.get(target_id)

        if source is None:
            raise ValueError(f"Source identity '{source_id}' not found")
        if target is None:
            raise ValueError(f"Target identity '{target_id}' not found")
        if source_id == target_id:
            raise ValueError("Cannot merge an identity into itself")
        if hasattr(source, '_retired') and source._retired:
            raise ValueError(f"Source identity '{source_id}' is retired and cannot be merged")
        if hasattr(target, '_retired') and target._retired:
            raise ValueError(f"Target identity '{target_id}' is retired and cannot be merged")

        conflicts: List[str] = []
        # Detect conflicting auth methods
        source_identifiers = {
            (m.method_type, m.identifier) for m in source.auth_methods
        }
        for m in target.auth_methods:
            if (m.method_type, m.identifier) in source_identifiers:
                conflicts.append(
                    f"Duplicate auth method '{m.method_type}:{m.identifier}' "
                    f"exists on both identities"
                )

        return IdentityMergePlan(
            source_id=source_id,
            target_id=target_id,
            source_display_name=getattr(source, 'display_name', ''),
            target_display_name=getattr(target, 'display_name', ''),
            auth_methods_to_transfer=len(source.auth_methods),
            evidence_count_source=len(source.evidence),
            evidence_count_target=len(target.evidence) + len(source.evidence),
            potential_conflicts=conflicts,
        )

    def merge(
        self,
        source_id: str,
        target_id: str,
        reason: str = "",
        actor: str = "system",
        force: bool = False,
    ) -> IdentityAuditEntry:
        """Merge source identity INTO target identity.

        The source identity is retired and its auth methods + evidence
        are transferred to the target. Source becomes permanently inactive.

        Args:
            source_id: Identity to merge into target
            target_id: Identity that will absorb the source
            reason: Why the merge is being performed
            actor: Who or what is performing the merge
            force: If True, skip conflict checks and merge anyway

        Returns:
            IdentityAuditEntry recording the merge

        Raises:
            ValueError: If either identity doesn't exist or merge is invalid
        """
        source = self._store.get(source_id)
        target = self._store.get(target_id)

        if source is None:
            raise ValueError(f"Source identity '{source_id}' not found")
        if target is None:
            raise ValueError(f"Target identity '{target_id}' not found")
        if source_id == target_id:
            raise ValueError("Cannot merge an identity into itself")
        if hasattr(source, '_retired') and source._retired:
            raise ValueError(f"Source identity '{source_id}' is retired and cannot be merged")
        if hasattr(target, '_retired') and target._retired:
            raise ValueError(f"Target identity '{target_id}' is retired and cannot be merged")

        if not force:
            plan = self.plan_merge(source_id, target_id)
            if plan.potential_conflicts:
                raise ValueError(
                    f"Merge conflicts detected: {'; '.join(plan.potential_conflicts)}. "
                    f"Use force=True to override."
                )

        # Transfer auth methods
        transferred_count = 0
        for method in source.auth_methods:
            if not target.has_auth_method(method.method_type, method.identifier):
                target.add_auth_method(method)
                transferred_count += 1

        # Transfer evidence refs
        for ev in source.evidence:
            target.add_evidence(ev)

        # Retire source identity
        source._retired = True
        source._retired_at = datetime.now(timezone.utc).isoformat()

        # Create audit entry (I-02: merge preserves evidence)
        self._audit_counter += 1
        entry = IdentityAuditEntry(
            audit_id=f"audit_merge_{self._audit_counter}",
            action=AuditAction.MERGE,
            identity_id=target_id,
            secondary_id=source_id,
            reason=reason or f"Merged into '{target_id}'",
            actor=actor,
            details={
                "source_display_name": getattr(source, 'display_name', ''),
                "target_display_name": getattr(target, 'display_name', ''),
                "auth_methods_transferred": transferred_count,
                "evidence_transferred": len(source.evidence),
            },
        )
        self._audit_log.append(entry)
        return entry

    # ---- Split ---------------------------------------------------------

    def plan_split(
        self,
        identity_id: str,
        partitions: List[IdentitySplitPartition],
    ) -> IdentitySplitPlan:
        """Preview a split operation before executing it.

        Args:
            identity_id: Identity to split
            partitions: Desired partition assignments

        Returns:
            IdentitySplitPlan showing what will happen
        """
        identity = self._store.get(identity_id)
        if identity is None:
            raise ValueError(f"Identity '{identity_id}' not found")
        if hasattr(identity, '_retired') and identity._retired:
            raise ValueError(f"Identity '{identity_id}' is retired and cannot be split")

        # Count assigned vs unassigned
        assigned_auth_count = sum(
            len(p.auth_methods) for p in partitions
        )
        assigned_ev_count = sum(
            len(p.evidence) for p in partitions
        )

        return IdentitySplitPlan(
            source_id=identity_id,
            partitions=list(partitions),
            unassigned_auth_methods=len(identity.auth_methods) - assigned_auth_count,
            unassigned_evidence=len(identity.evidence) - assigned_ev_count,
        )

    def split(
        self,
        identity_id: str,
        partitions: List[IdentitySplitPartition],
        reason: str = "",
        actor: str = "system",
    ) -> List[IdentityAuditEntry]:
        """Split an identity into multiple new identities.

        The original identity is retired. New identities are created
        with the specified auth methods and evidence partitions.

        Args:
            identity_id: Identity to split
            partitions: List of partitions to create
            reason: Why the split is being performed
            actor: Who or what is performing the split

        Returns:
            List of IdentityAuditEntry records (one per split + source retirement)

        Raises:
            ValueError: If the identity doesn't exist or is retired
        """
        identity = self._store.get(identity_id)
        if identity is None:
            raise ValueError(f"Identity '{identity_id}' not found")
        if hasattr(identity, '_retired') and identity._retired:
            raise ValueError(f"Identity '{identity_id}' is retired and cannot be split")
        if not partitions:
            raise ValueError("At least one partition is required for split")

        entries: List[IdentityAuditEntry] = []

        # Create new identities for each partition
        for i, partition in enumerate(partitions):
            new_name = partition.new_display_name or (
                f"{getattr(identity, 'display_name', 'Unknown')} (Part {i + 1})"
            )
            new_identity = SHUNYAIdentity(
                display_name=new_name,
            )
            # Transfer auth methods
            for method in partition.auth_methods:
                new_identity.add_auth_method(method)
            # Transfer evidence
            for ev in partition.evidence:
                new_identity.add_evidence(ev)
            # Store the new identity
            self._store._identities[new_identity.identity_id] = new_identity

            self._audit_counter += 1
            entry = IdentityAuditEntry(
                audit_id=f"audit_split_{self._audit_counter}",
                action=AuditAction.SPLIT,
                identity_id=new_identity.identity_id,
                secondary_id=identity_id,
                reason=reason or f"Split from '{identity_id}'",
                actor=actor,
                details={
                    "partition_index": i,
                    "auth_methods": len(partition.auth_methods),
                    "evidence": len(partition.evidence),
                    "new_display_name": new_name,
                },
            )
            self._audit_log.append(entry)
            entries.append(entry)

        # Retire original identity (I-03: split partitions evidence)
        identity._retired = True
        identity._retired_at = datetime.now(timezone.utc).isoformat()

        self._audit_counter += 1
        retire_entry = IdentityAuditEntry(
            audit_id=f"audit_split_retire_{self._audit_counter}",
            action=AuditAction.RETIRE,
            identity_id=identity_id,
            reason=reason or f"Split into {len(partitions)} partitions",
            actor=actor,
            details={
                "partition_count": len(partitions),
                "original_display_name": getattr(identity, 'display_name', ''),
            },
        )
        self._audit_log.append(retire_entry)
        entries.append(retire_entry)

        return entries

    # ---- Retire --------------------------------------------------------

    def retire(
        self,
        identity_id: str,
        reason: str = "",
        actor: str = "system",
    ) -> IdentityAuditEntry:
        """Permanently retire an identity (I-04: retired identities never reused).

        The identity is marked as retired but preserved in the store.
        It cannot be merged, split, or accept new auth methods.

        Args:
            identity_id: Identity to retire
            reason: Why the identity is being retired
            actor: Who or what is retiring the identity

        Returns:
            IdentityAuditEntry recording the retirement

        Raises:
            ValueError: If the identity doesn't exist or is already retired
        """
        identity = self._store.get(identity_id)
        if identity is None:
            raise ValueError(f"Identity '{identity_id}' not found")
        if hasattr(identity, '_retired') and identity._retired:
            raise ValueError(f"Identity '{identity_id}' is already retired")

        # Mark as retired (I-04)
        identity._retired = True
        identity._retired_at = datetime.now(timezone.utc).isoformat()

        self._audit_counter += 1
        entry = IdentityAuditEntry(
            audit_id=f"audit_retire_{self._audit_counter}",
            action=AuditAction.RETIRE,
            identity_id=identity_id,
            reason=reason or "No reason specified",
            actor=actor,
            details={
                "display_name": getattr(identity, 'display_name', ''),
                "auth_methods_count": len(identity.auth_methods),
                "evidence_count": len(identity.evidence),
            },
        )
        self._audit_log.append(entry)
        return entry

    # ---- Restore -------------------------------------------------------

    def restore(
        self,
        identity_id: str,
        reason: str = "",
        actor: str = "system",
    ) -> IdentityAuditEntry:
        """Restore a retired identity to active status.

        Args:
            identity_id: Identity to restore
            reason: Why the identity is being restored
            actor: Who or what is restoring the identity

        Returns:
            IdentityAuditEntry recording the restoration

        Raises:
            ValueError: If the identity doesn't exist or is not retired
        """
        identity = self._store.get(identity_id)
        if identity is None:
            raise ValueError(f"Identity '{identity_id}' not found")
        if not hasattr(identity, '_retired') or not identity._retired:
            raise ValueError(f"Identity '{identity_id}' is not retired")

        identity._retired = False
        identity._retired_at = None

        self._audit_counter += 1
        entry = IdentityAuditEntry(
            audit_id=f"audit_restore_{self._audit_counter}",
            action=AuditAction.RESTORE,
            identity_id=identity_id,
            reason=reason or "Restored to active status",
            actor=actor,
            details={
                "display_name": getattr(identity, 'display_name', ''),
            },
        )
        self._audit_log.append(entry)
        return entry

    # ---- Query ---------------------------------------------------------

    def get_audit_trail(self, identity_id: str) -> List[IdentityAuditEntry]:
        """Get all audit events for a specific identity.

        Args:
            identity_id: Identity to query

        Returns:
            List of audit entries involving this identity (primary or secondary)
        """
        return [
            entry for entry in self._audit_log
            if entry.identity_id == identity_id
            or entry.secondary_id == identity_id
        ]

    def is_retired(self, identity_id: str) -> bool:
        """Check if an identity is retired.

        Args:
            identity_id: Identity to check

        Returns:
            True if the identity is retired
        """
        identity = self._store.get(identity_id)
        if identity is None:
            return False
        return hasattr(identity, '_retired') and bool(identity._retired)

    def get_active_identities(self) -> List[SHUNYAIdentity]:
        """Get all active (non-retired) identities from the store.

        I-04: Retired identities are never returned as active.
        """
        return [
            identity for identity in self._store.all()
            if not (hasattr(identity, '_retired') and identity._retired)
        ]