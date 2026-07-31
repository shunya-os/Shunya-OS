"""Tests for SHUNYA Kernel — Identity Governance (E-002).

Architecture references:
    UNIVERSAL_ONTOLOGY.md §3 — Identity
    UNIVERSAL_ONTOLOGY.md §3.5 — Identity merge, split, deletion
    IMPLEMENTATION_MASTER_PLAN.md — E-002 Identity Engine

Constitutional invariants tested:
    I-01: Identities are permanent (never truly deleted, only retired)
    I-02: Merge preserves evidence
    I-03: Split partitions evidence
    I-04: Retired identities are never reused
"""

import pytest
from app.kernel.identity import (
    SHUNYAIdentity, IdentityStore, AuthenticationMethod,
    AuthMethodType, get_identity_store, reset_identity_store,
)
from app.kernel.identity_governance import (
    IdentityGovernance, IdentityAuditEntry, AuditAction,
    IdentityMergePlan, IdentitySplitPlan, IdentitySplitPartition,
)
from app.kernel.object import EvidenceRef


# =========================================================================
# Identity Governance — Merge Tests
# =========================================================================

class TestIdentityMerge:
    """UNIVERSAL_ONTOLOGY.md §3.5 — Identity merge."""

    def setup_method(self):
        reset_identity_store()

    def test_plan_merge_returns_preview(self):
        """plan_merge returns a preview without side effects."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")

        plan = gov.plan_merge(alice.identity_id, bob.identity_id)
        assert isinstance(plan, IdentityMergePlan)
        assert plan.source_id == alice.identity_id
        assert plan.target_id == bob.identity_id
        assert plan.auth_methods_to_transfer == 1
        # No side effects — identities unchanged
        assert not gov.is_retired(alice.identity_id)

    def test_merge_transfers_auth_methods(self):
        """I-02: Merge transfers auth methods to target."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        alice.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.PHONE.value,
            identifier="+1111111111",
        ))
        bob = store.create("Bob", "bob@test.com")

        gov.merge(alice.identity_id, bob.identity_id, reason="Duplicate")

        # Bob should have Alice's auth methods
        bob_refreshed = store.get(bob.identity_id)
        assert bob_refreshed is not None
        assert bob_refreshed.has_auth_method(
            AuthMethodType.EMAIL.value, "alice@test.com"
        )
        assert bob_refreshed.has_auth_method(
            AuthMethodType.PHONE.value, "+1111111111"
        )

    def test_merge_retires_source(self):
        """I-01 + I-04: Merge retires the source identity permanently."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")

        gov.merge(alice.identity_id, bob.identity_id)
        assert gov.is_retired(alice.identity_id)
        assert not gov.is_retired(bob.identity_id)

    def test_merge_preserves_evidence(self):
        """I-02: Merge preserves evidence from both identities."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        alice.add_evidence(EvidenceRef(
            object_id="obj_001", object_type="Person",
            field="name", confidence=0.95,
        ))
        bob = store.create("Bob", "bob@test.com")
        bob.add_evidence(EvidenceRef(
            object_id="obj_002", object_type="Person",
            field="email", confidence=0.9,
        ))

        gov.merge(alice.identity_id, bob.identity_id)

        bob_refreshed = store.get(bob.identity_id)
        assert bob_refreshed is not None
        # Both evidence refs should be on the target
        evidence_object_ids = {ev.object_id for ev in bob_refreshed.evidence}
        assert "obj_001" in evidence_object_ids
        assert "obj_002" in evidence_object_ids

    def test_merge_into_self_raises(self):
        """Cannot merge an identity into itself."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        with pytest.raises(ValueError, match="into itself"):
            gov.merge(alice.identity_id, alice.identity_id)

    def test_merge_nonexistent_raises(self):
        """Merge of nonexistent identity raises."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        with pytest.raises(ValueError, match="not found"):
            gov.merge("nonexistent", alice.identity_id)
        with pytest.raises(ValueError, match="not found"):
            gov.merge(alice.identity_id, "nonexistent")

    def test_merge_retired_source_raises(self):
        """Cannot merge a retired identity."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")
        gov.retire(alice.identity_id)
        with pytest.raises(ValueError, match="retired"):
            gov.merge(alice.identity_id, bob.identity_id)

    def test_merge_conflict_detection(self):
        """Merge conflict detection catches duplicate auth methods."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "shared@test.com")
        bob = store.create("Bob", "shared@test.com")

        with pytest.raises(ValueError, match="conflict"):
            gov.merge(alice.identity_id, bob.identity_id)

    def test_merge_force_overrides_conflict(self):
        """Merge with force=True bypasses conflict detection."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "shared@test.com")
        bob = store.create("Bob", "shared@test.com")

        entry = gov.merge(alice.identity_id, bob.identity_id, force=True)
        assert entry.action == AuditAction.MERGE
        assert gov.is_retired(alice.identity_id)

    def test_merge_produces_audit_entry(self):
        """I-02: Merge produces an auditable record."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")

        entry = gov.merge(
            alice.identity_id, bob.identity_id,
            reason="Duplicate identity", actor="admin",
        )
        assert entry.action == AuditAction.MERGE
        assert entry.identity_id == bob.identity_id
        assert entry.secondary_id == alice.identity_id
        assert entry.reason == "Duplicate identity"
        assert entry.actor == "admin"


# =========================================================================
# Identity Governance — Split Tests
# =========================================================================

class TestIdentitySplit:
    """UNIVERSAL_ONTOLOGY.md §3.5 — Identity split."""

    def setup_method(self):
        reset_identity_store()

    def test_split_creates_new_identities(self):
        """I-03: Split creates new identities from partitions."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        alice.add_auth_method(AuthenticationMethod(
            method_type=AuthMethodType.PHONE.value,
            identifier="+1111111111",
        ))
        alice.add_evidence(EvidenceRef(
            object_id="obj_001", object_type="Document",
        ))
        alice.add_evidence(EvidenceRef(
            object_id="obj_002", object_type="Document",
        ))

        # Split into work and personal partitions
        work_partition = IdentitySplitPartition(
            auth_methods=[alice.auth_methods[0]],  # email
            evidence=[alice.evidence[0]],           # obj_001
            new_display_name="Alice (Work)",
        )
        personal_partition = IdentitySplitPartition(
            auth_methods=[alice.auth_methods[1]],   # phone
            evidence=[alice.evidence[1]],            # obj_002
            new_display_name="Alice (Personal)",
        )

        entries = gov.split(
            alice.identity_id,
            [work_partition, personal_partition],
            reason="Separate work and personal",
            actor="system",
        )

        # Original should be retired
        assert gov.is_retired(alice.identity_id)

        # Should have entries: 2 splits + 1 retire
        assert len(entries) == 3
        split_entries = [e for e in entries if e.action == AuditAction.SPLIT]
        retire_entries = [e for e in entries if e.action == AuditAction.RETIRE]
        assert len(split_entries) == 2
        assert len(retire_entries) == 1

        # New identities should be in the store
        all_ids = [e.identity_id for e in split_entries]
        for new_id in all_ids:
            new_identity = store.get(new_id)
            assert new_identity is not None
            assert not gov.is_retired(new_id)

    def test_split_at_least_one_partition(self):
        """Split requires at least one partition."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        with pytest.raises(ValueError, match="At least one partition"):
            gov.split(alice.identity_id, [])

    def test_split_nonexistent_raises(self):
        """Split of nonexistent identity raises."""
        gov = IdentityGovernance(get_identity_store())
        with pytest.raises(ValueError, match="not found"):
            gov.split("nonexistent", [IdentitySplitPartition()])

    def test_split_retired_raises(self):
        """Cannot split a retired identity."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        gov.retire(alice.identity_id)
        with pytest.raises(ValueError, match="retired"):
            gov.split(alice.identity_id, [IdentitySplitPartition()])


# =========================================================================
# Identity Governance — Retire / Restore Tests
# =========================================================================

class TestIdentityRetire:
    """UNIVERSAL_ONTOLOGY.md §3.5 — Identity retirement."""

    def setup_method(self):
        reset_identity_store()

    def test_retire_marks_identity(self):
        """I-04: Retire marks an identity as permanently retired."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")

        entry = gov.retire(alice.identity_id, reason="GDPR erasure request")
        assert entry.action == AuditAction.RETIRE
        assert gov.is_retired(alice.identity_id)

    def test_retire_twice_raises(self):
        """Cannot retire an already retired identity."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        gov.retire(alice.identity_id)
        with pytest.raises(ValueError, match="already retired"):
            gov.retire(alice.identity_id)

    def test_retired_not_in_active_list(self):
        """I-04: Retired identities never appear in active list."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")

        gov.retire(alice.identity_id)
        active = gov.get_active_identities()
        active_ids = [i.identity_id for i in active]
        assert alice.identity_id not in active_ids
        assert bob.identity_id in active_ids

    def test_retired_still_in_store(self):
        """I-01: Retired identities are still in the store (not deleted)."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        aid = alice.identity_id
        gov.retire(aid)
        assert store.get(aid) is not None

    def test_restore_reactivates_retired(self):
        """Restore brings a retired identity back to active."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        gov.retire(alice.identity_id)
        assert gov.is_retired(alice.identity_id)

        entry = gov.restore(alice.identity_id, reason="Reinstated")
        assert entry.action == AuditAction.RESTORE
        assert not gov.is_retired(alice.identity_id)

    def test_restore_non_retired_raises(self):
        """Cannot restore an identity that is not retired."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        with pytest.raises(ValueError, match="not retired"):
            gov.restore(alice.identity_id)

    def test_retire_nonexistent_raises(self):
        """Retire of nonexistent identity raises."""
        gov = IdentityGovernance(get_identity_store())
        with pytest.raises(ValueError, match="not found"):
            gov.retire("nonexistent")


# =========================================================================
# Audit Trail Tests
# =========================================================================

class TestAuditTrail:
    """All governance operations are auditable."""

    def setup_method(self):
        reset_identity_store()

    def test_audit_log_tracks_all_operations(self):
        """Every governance operation produces an audit entry."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")

        gov.merge(alice.identity_id, bob.identity_id)
        assert len(gov.audit_log) == 1

        gov.retire(bob.identity_id)
        assert len(gov.audit_log) == 2

    def test_get_audit_trail_for_identity(self):
        """Audit trail can be queried per identity."""
        store = get_identity_store()
        gov = IdentityGovernance(store)
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")
        charlie = store.create("Charlie", "charlie@test.com")

        gov.merge(alice.identity_id, bob.identity_id)
        gov.retire(charlie.identity_id)

        # Alice should have 1 audit entry (merge as secondary)
        alice_trail = gov.get_audit_trail(alice.identity_id)
        assert len(alice_trail) == 1
        assert alice_trail[0].action == AuditAction.MERGE

        # Charlie should have 1 audit entry (retire as primary)
        charlie_trail = gov.get_audit_trail(charlie.identity_id)
        assert len(charlie_trail) == 1
        assert charlie_trail[0].action == AuditAction.RETIRE

    def test_audit_entry_to_dict(self):
        """Audit entries serialize to dict."""
        entry = IdentityAuditEntry(
            audit_id="audit_001",
            action=AuditAction.MERGE,
            identity_id="sid_target",
            secondary_id="sid_source",
            reason="Duplicate",
            actor="admin",
            details={"auth_methods_transferred": 2},
        )
        d = entry.to_dict()
        assert d["audit_id"] == "audit_001"
        assert d["action"] == "merge"
        assert d["identity_id"] == "sid_target"
        assert d["details"]["auth_methods_transferred"] == 2


# =========================================================================
# Integration Tests — Merge + Governance lifecycle
# =========================================================================

class TestIdentityGovernanceIntegration:
    """End-to-end identity lifecycle with governance."""

    def setup_method(self):
        reset_identity_store()

    def test_full_lifecycle_merge_then_retire(self):
        """Identity lifecycle: create → merge → retire → restore."""
        store = get_identity_store()
        gov = IdentityGovernance(store)

        # Create identities
        alice = store.create("Alice", "alice@test.com")
        bob = store.create("Bob", "bob@test.com")

        # Plan merge
        plan = gov.plan_merge(alice.identity_id, bob.identity_id)
        assert plan.auth_methods_to_transfer == 1

        # Execute merge
        gov.merge(alice.identity_id, bob.identity_id,
                   reason="Duplicate detected", actor="system")

        # Source is retired, target has both auth methods
        assert gov.is_retired(alice.identity_id)
        bob_refreshed = store.get(bob.identity_id)
        assert bob_refreshed is not None
        assert bob_refreshed.has_auth_method(
            AuthMethodType.EMAIL.value, "alice@test.com"
        )

        # Retire target
        gov.retire(bob.identity_id, reason="Account closed")
        assert gov.is_retired(bob.identity_id)

        # Verify audit trail — bob was the merge target (identity_id) so both merge and retire appear
        bob_trail = gov.get_audit_trail(bob.identity_id)
        assert len(bob_trail) == 2

        # Restore target
        gov.restore(bob.identity_id, reason="Reopened")
        assert not gov.is_retired(bob.identity_id)

    def test_multiple_merges_into_same_target(self):
        """Multiple identities can be merged into a single target."""
        store = get_identity_store()
        gov = IdentityGovernance(store)

        target = store.create("Target", "target@test.com")
        sources = []
        for i in range(3):
            identity = store.create(f"Source{i}", f"source{i}@test.com")
            sources.append(identity)

        for source in sources:
            gov.merge(source.identity_id, target.identity_id,
                       reason=f"Merging Source", force=True)

        target_refreshed = store.get(target.identity_id)
        assert target_refreshed is not None
        # Target should have all 4 auth methods (1 original + 3 sources)
        assert len(target_refreshed.auth_methods) == 4

        # All sources are retired
        for source in sources:
            assert gov.is_retired(source.identity_id)

        # Audit trail has 3 merge entries
        assert len(gov.audit_log) == 3

    def test_merge_plan_empty_source(self):
        """Merging an identity with no auth methods still works."""
        store = get_identity_store()
        gov = IdentityGovernance(store)

        alice = store.create("Alice", "alice@test.com")
        empty_id = store.create("Empty", "")  # No email

        plan = gov.plan_merge(empty_id.identity_id, alice.identity_id)
        assert plan.auth_methods_to_transfer == 0

        gov.merge(empty_id.identity_id, alice.identity_id,
                   reason="Empty identity cleanup")
        assert gov.is_retired(empty_id.identity_id)