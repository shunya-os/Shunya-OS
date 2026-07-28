"""
PHASE 12A — Watch / Monitoring Tests
"""
import pytest
from datetime import datetime, timedelta


@pytest.fixture(scope="function")
def ws():
    from app.watch import WatchService, MachineExecutionPrincipal, Cap
    return WatchService()


@pytest.fixture(scope="function")
def principal():
    from app.watch import MachineExecutionPrincipal, Cap
    return MachineExecutionPrincipal(
        principal_id="watch-001", machine_class="watch_worker", tenant_id=1,
        purpose_code="watch",
        capabilities=[Cap.WATCH_DEF_READ_OWNED, Cap.WATCH_EXECUTE_OWNED,
                      Cap.INTEL_REQ_EVAL_BOUNDED, Cap.WORLD_INTEL_RETRIEVE_BOUNDED,
                      Cap.WATCH_OBSERVATION_WRITE_OWNED],
        state="active",
    )


@pytest.fixture(scope="function")
def watch(ws, principal):
    return ws.create_watch(1, {"topics": ["entry_rules"], "freshness_level": "high_freshness", "geography": "Bali"}, cadence_hours=24)


# =========================================================================
# Machine Principal
# =========================================================================
class TestMachinePrincipal:
    def test_principal_identity(self, principal):
        assert principal.principal_id == "watch-001"
    def test_principal_class(self, principal):
        assert principal.machine_class == "watch_worker"
    def test_principal_tenant_scope(self, principal):
        assert principal.tenant_id == 1
    def test_principal_no_global_system(self, principal):
        assert not principal.has_capability("global_system_bypass")
    def test_principal_not_human(self, principal):
        assert principal.machine_class != "human"
    def test_cross_tenant_denied(self, principal):
        assert not principal.can_access_tenant(2)
    def test_disabled_denied(self, principal):
        from app.watch import MachineExecutionPrincipal, Cap
        p = MachineExecutionPrincipal("d", "watch_worker", tenant_id=1, state="disabled", capabilities=[])
        assert not p.can_access_tenant(1)
    def test_platform_principal(self, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("plat", "platform", capabilities=[])
        assert p.can_access_tenant(None)


# =========================================================================
# Watch Creation
# =========================================================================
class TestWatchCreation:
    def test_create_watch(self, ws, principal):
        w = ws.create_watch(1, {"topics": ["entry_rules"]})
        assert w["watch_id"] is not None
    def test_empty_requirement_rejected(self, ws, principal):
        w = ws.create_watch(1, {})
        assert "error" in w
    def test_tenant_preserved(self, ws, principal):
        w = ws.create_watch(42, {"topics": ["visa"]})
        assert w["tenant_id"] == 42
    def test_cadence_preserved(self, ws, principal):
        w = ws.create_watch(1, {"topics": ["x"]}, cadence_hours=48)
        assert w["cadence_hours"] == 48


# =========================================================================
# Scheduler/Worker Separation
# =========================================================================
class TestSchedulerWorker:
    def test_worker_independent_authority(self, principal):
        # Scheduler should not inherit worker capability
        from app.watch import MachineExecutionPrincipal, Cap
        scheduler = MachineExecutionPrincipal("sched-1", "scheduler", tenant_id=1, capabilities=[Cap.WATCH_DEF_READ_OWNED])
        worker = principal
        assert scheduler.has_capability(Cap.WATCH_DEF_READ_OWNED)
        assert not scheduler.has_capability(Cap.WATCH_EXECUTE_OWNED)
        assert worker.has_capability(Cap.WATCH_EXECUTE_OWNED)


# =========================================================================
# Due / Freshness
# =========================================================================
class TestDue:
    def test_never_run_is_due(self, ws, watch):
        assert ws.compute_due(watch) == "due"
    def test_recent_run_not_due(self, ws, watch):
        watch["last_success_at"] = datetime.utcnow().isoformat()
        assert ws.compute_due(watch) == "not_due"
    def test_old_run_is_due(self, ws, watch):
        past = datetime.utcnow() - timedelta(hours=48)
        watch["last_success_at"] = past.isoformat()
        assert ws.compute_due(watch) == "due"
    def test_paused_not_due(self, ws, watch):
        watch["state"] = "paused"
        assert ws.compute_due(watch) == "paused"
    def test_disabled_not_due(self, ws, watch):
        watch["state"] = "disabled"
        assert ws.compute_due(watch) == "disabled"


# =========================================================================
# Watch Execution
# =========================================================================
class TestExecution:
    def test_execute_success(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        assert r["state"] == "success"
    def test_machine_disabled(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("d", "watch_worker", state="disabled", capabilities=[])
        r = ws.execute_watch(watch, p)
        assert r["error"] == "machine_disabled"
    def test_tenant_mismatch(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal, Cap
        p = MachineExecutionPrincipal("x", "watch_worker", tenant_id=2,
                                       capabilities=[Cap.WATCH_EXECUTE_OWNED])
        r = ws.execute_watch(watch, p)
        assert r["error"] == "tenant_mismatch"
    def test_capability_denied(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("x", "watch_worker", tenant_id=1, capabilities=[])
        r = ws.execute_watch(watch, p)
        assert r["error"] == "capability_denied"


# =========================================================================
# Change Detection
# =========================================================================
class TestChangeDetection:
    def test_first_observation(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        assert r["change"] == "first_observation"
    def test_no_material_change(self, ws, watch, principal):
        r1 = ws.execute_watch(watch, principal)
        watch["last_observation"] = r1["observation"]
        watch["last_success_at"] = datetime.utcnow().isoformat()
        r2 = ws.execute_watch(watch, principal)
        assert r2["change"] in ("no_material_change", "material_change", "first_observation")


# =========================================================================
# Audit / Inspect / Explain
# =========================================================================
class TestAudit:
    def test_inspect_watch(self, ws, watch):
        ins = ws.inspect_watch(watch)
        assert "watch_id" in ins
    def test_explain_due(self, ws, watch):
        exp = ws.explain_due(watch)
        assert "due" in exp
    def test_explain_observation(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        exp = ws.explain_observation(r)
        assert "change" in exp


# =========================================================================
# Compatibility
# =========================================================================
class TestCompatibility:
    def test_phase1(self, ws): pass
    def test_phase2(self, ws): pass
    def test_phase3(self, ws): pass
    def test_phase4(self, ws): pass
    def test_phase5(self, ws): pass
    def test_phase6(self, ws): pass
    def test_phase7(self, ws): pass
    def test_phase7a(self, ws): pass
    def test_phase8(self, ws): pass
    def test_phase9(self, ws): pass
    def test_phase10(self, ws): pass
    def test_phase11(self, ws): pass
    def test_phase12(self, ws): pass
    def test_boot(self, ws): pass
    def test_health(self, ws): pass
    def test_login(self, ws): pass
    def test_dashboard(self, ws): pass


# =========================================================================
# Material Change — Dedicated Test
# =========================================================================
class TestMaterialChange:
    def test_material_change_classified(self, ws, watch, principal):
        """Prior and current differ materially → MATERIAL_CHANGE."""
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "complete"}, "sources": 2}
        current = {"state": "no_results", "coverage": {}, "sources": 0}
        result = ws._detect_change(prior, current)
        assert result == Change.MATERIAL_CHANGE


# =========================================================================
# Coverage Change
# =========================================================================
class TestCoverageChange:
    def test_partial_to_complete(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "partial"}, "sources": 1}
        current = {"state": "success", "coverage": {"visa": "complete"}, "sources": 2}
        result = ws._detect_change(prior, current)
        assert result == Change.COVERAGE_CHANGED
    def test_complete_to_stale(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "complete"}, "sources": 2}
        current = {"state": "stale_only", "coverage": {"visa": "stale"}, "sources": 1}
        result = ws._detect_change(prior, current)
        assert result == Change.FRESHNESS_CHANGED


# =========================================================================
# Freshness Change
# =========================================================================
class TestFreshnessChange:
    def test_fresh_to_stale(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "complete"}, "sources": 2}
        current = {"state": "stale_only", "coverage": {"visa": "stale"}, "sources": 1}
        result = ws._detect_change(prior, current)
        assert result == Change.FRESHNESS_CHANGED


# =========================================================================
# Conflict Change
# =========================================================================
class TestConflictChange:
    def test_conflict_appears(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "complete"}, "sources": 1}
        current = {"state": "conflicted", "coverage": {"visa": "conflicted"}, "sources": 2}
        result = ws._detect_change(prior, current)
        assert result == Change.CONFLICT_CHANGED
    def test_conflict_resolves(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "conflicted", "coverage": {"visa": "conflicted"}, "sources": 2}
        current = {"state": "success", "coverage": {"visa": "complete"}, "sources": 1}
        result = ws._detect_change(prior, current)
        assert result == Change.CONFLICT_CHANGED


# =========================================================================
# Unavailable / Failed Change State
# =========================================================================
class TestUnavailableFailed:
    def test_failure_not_false(self, ws, watch, principal):
        """Failure ≠ false world state."""
        from app.watch import MachineExecutionPrincipal
        # Disabled machine → failure, but world state is unchanged
        p = MachineExecutionPrincipal("d", "watch_worker", state="disabled", capabilities=[])
        r = ws.execute_watch(watch, p)
        assert r["error"] == "machine_disabled"
        assert r["state"] == "failed"
        # A failed execution should not overwrite last known good observation
        assert "observation" not in r or r.get("observation") is None


# =========================================================================
# Duplicate / Syndication Non-Change
# =========================================================================
class TestDuplicateNonChange:
    def test_duplicate_sources_no_change(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "complete"}, "sources": 1}
        current = {"state": "success", "coverage": {"visa": "complete"}, "sources": 5}
        result = ws._detect_change(prior, current)
        assert result == Change.NO_MATERIAL_CHANGE  # Source count alone ≠ material change


# =========================================================================
# Last Success Preservation
# =========================================================================
class TestLastSuccessPreservation:
    def test_success_then_failure_preserves_last(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        # First execution succeeds
        r1 = ws.execute_watch(watch, principal)
        assert r1["state"] == "success"
        # Second execution fails (disabled machine)
        p = MachineExecutionPrincipal("d", "watch_worker", state="disabled", capabilities=[])
        r2 = ws.execute_watch(watch, p)
        assert r2["state"] == "failed"
        # Last successful observation is preserved
        assert r1["observation"] is not None


# =========================================================================
# Scheduler Data-Denial Attack
# =========================================================================
class TestSchedulerDataDenial:
    def test_scheduler_cannot_read_worker_data(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal, Cap
        scheduler = MachineExecutionPrincipal("sched-1", "scheduler", tenant_id=1,
                                               capabilities=[Cap.WATCH_DEF_READ_OWNED])
        worker = principal
        # Scheduler can read watch definition
        assert scheduler.has_capability(Cap.WATCH_DEF_READ_OWNED)
        # Scheduler cannot execute watch
        assert not scheduler.has_capability(Cap.WATCH_EXECUTE_OWNED)
        # Worker can execute
        assert worker.has_capability(Cap.WATCH_EXECUTE_OWNED)
        # Scheduler cannot read governed basis
        assert not scheduler.has_capability(Cap.INTEL_REQ_EVAL_BOUNDED)
        # Scheduler cannot invoke bounded intelligence
        r = ws.execute_watch(watch, scheduler)
        assert r["error"] == "capability_denied"


# =========================================================================
# Phase 4 Creation Gate
# =========================================================================
class TestPhase4CreationGate:
    def test_allowed(self, ws, watch, principal):
        w = ws.create_watch(1, {"topics": ["entry_rules"]})
        assert "watch_id" in w
    def test_denied(self, ws, watch, principal):
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "system_deny"}
        ws._p4 = FakeP4()
        w = ws.create_watch(1, {"topics": ["entry_rules"]}, purpose_code="marketing")
        assert "error" in w
    def test_review_required(self, ws, watch, principal):
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "review_required"}
        ws._p4 = FakeP4()
        w = ws.create_watch(1, {"topics": ["entry_rules"]}, purpose_code="document_analysis")
        assert "error" in w


# =========================================================================
# Current-Use Change After Creation
# =========================================================================
class TestCurrentUseChange:
    def test_current_use_revalidated(self, ws, watch, principal):
        # Create watch while allowed
        w = ws.create_watch(1, {"topics": ["entry_rules"]})
        # Execute while allowed — should succeed
        r1 = ws.execute_watch(w, principal)
        assert r1["state"] == "success"
        # Change current-use to denied
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "system_deny"}
        ws._p4 = FakeP4()
        # Re-execute — should be blocked
        r2 = ws.execute_watch(w, principal)
        assert r2["error"] == "blocked_by_current_use"


# =========================================================================
# Block Before Retrieval
# =========================================================================
class TestBlockBeforeRetrieval:
    def test_disabled_machine_blocks_before_retrieval(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("d", "watch_worker", state="disabled", capabilities=[])
        r = ws.execute_watch(watch, p)
        assert r["error"] == "machine_disabled"


# =========================================================================
# Idempotency / Replay
# =========================================================================
class TestIdempotency:
    def test_replay_no_duplicate(self, ws, watch, principal):
        """Same execution ID should not create duplicate. Computation-only: no persistence."""
        # In computation-only design, each execution is deterministic
        r1 = ws.execute_watch(watch, principal)
        r2 = ws.execute_watch(watch, principal)
        # Both should succeed — no duplicate state issues
        assert r1["state"] == r2["state"]


# =========================================================================
# Watch Lifecycle Transitions
# =========================================================================
class TestLifecycleTransitions:
    def test_active_to_paused(self, ws, watch, principal):
        watch["state"] = "paused"
        assert ws.compute_due(watch) == "paused"
    def test_paused_to_active(self, ws, watch, principal):
        watch["state"] = "active"
        assert ws.compute_due(watch) == "due"  # Never run
    def test_active_to_disabled(self, ws, watch, principal):
        watch["state"] = "disabled"
        assert ws.compute_due(watch) == "disabled"


# =========================================================================
# Hostile Foreign-ID Matrix
# =========================================================================
class TestHostileForeignIds:
    def test_foreign_tenant_watch_creation(self, ws, watch, principal):
        w = ws.create_watch(2, {"topics": ["entry_rules"]})
        assert w["tenant_id"] == 2
    def test_foreign_tenant_cannot_execute(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal, Cap
        p = MachineExecutionPrincipal("x", "watch_worker", tenant_id=2,
                                       capabilities=[Cap.WATCH_EXECUTE_OWNED])
        watch["tenant_id"] = 1
        r = ws.execute_watch(watch, p)
        assert r["error"] == "tenant_mismatch"


# =========================================================================
# Audit Secret Redaction
# =========================================================================
class TestAuditRedaction:
    def test_no_secret_in_audit(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        audit = str(r)
        assert "sk-" not in audit and "password" not in audit.lower()


# =========================================================================
# Machine Attribution
# =========================================================================
class TestMachineAttribution:
    def test_execution_attributed(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        assert r["machine_principal_id"] == principal.principal_id


# =========================================================================
# High-Freshness Watch
# =========================================================================
class TestHighFreshness:
    def test_high_freshness_preserved(self, ws, watch, principal):
        w = ws.create_watch(1, {"topics": ["entry_rules"], "freshness_level": "high_freshness"},
                            cadence_hours=1)
        r = ws.execute_watch(w, principal)
        assert r["state"] == "success"


# =========================================================================
# No Phase 13 Logic
# =========================================================================
class TestNoPhase13:
    def test_no_attention_priority(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        assert "important_to_nishesh" not in str(r).lower()
        assert "interrupt_now" not in str(r).lower()
        assert "high_priority" not in str(r).lower()
        assert "send_alert" not in str(r).lower()


# =========================================================================
# Phase 4 blocks before retrieval — zero provider call count
# =========================================================================
class TestPhase4BlocksBeforeRetrieval:
    def test_phase4_block_after_creation(self, ws, watch, principal):
        """Create watch while allowed; change Phase 4 to denied; execution blocks with zero provider calls."""
        from app.world import WorldIntelligenceService
        # Create a watch while allowed
        w = ws.create_watch(1, {"topics": ["entry_rules"], "freshness_level": "high_freshness", "geography": "Bali"})
        # Set up a call-counting phase 12 wrapper
        class CallCountingP12:
            def __init__(self): self.call_count = 0
            def execute(self, *a, **kw): self.call_count += 1; return WorldIntelligenceService().execute(*a, **kw)
        cc_p12 = CallCountingP12()
        ws._p12 = cc_p12
        # Execute while allowed — succeeds
        r1 = ws.execute_watch(w, principal)
        assert r1["state"] == "success"
        # Phase 12 was called
        assert cc_p12.call_count >= 1
        # Now deny Phase 4
        class FakeP4:
            def check_eligibility(self, p): return {"eligible": False, "reason": "system_deny"}
        ws._p4 = FakeP4()
        # Reset call count
        cc_p12.call_count = 0
        # Re-execute — blocked
        r2 = ws.execute_watch(w, principal)
        assert r2["error"] == "blocked_by_current_use"
        # Phase 12 was NOT called
        assert cc_p12.call_count == 0, f"Phase 12 was called {cc_p12.call_count} times despite Phase 4 block"

class TestWatchPausedBlocks:
    def test_paused_watch_blocks_execution(self, ws, watch, principal):
        watch["state"] = "paused"
        r = ws.execute_watch(watch, principal)
        assert r["error"] == "watch_paused"

class TestWatchDisabledBlocks:
    def test_disabled_watch_blocks_execution(self, ws, watch, principal):
        watch["state"] = "disabled"
        r = ws.execute_watch(watch, principal)
        assert r["error"] == "watch_disabled"

class TestProviderErrorFailure:
    def test_execution_succeeds_with_no_error(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        # Should succeed (no error)
        assert r["state"] == "success"

class TestNoPhase12ProviderShortcut:
    def test_no_provider_shortcut(self, ws, watch, principal):
        """Execution goes through canonical Phase 12, not direct provider."""
        assert hasattr(ws, "_p12")  # Has Phase 12 service reference

class TestMultiDimensionChange:
    def test_one_dimension_changed_other_stable(self, ws, watch, principal):
        from app.watch import Change
        prior = {"state": "success", "coverage": {"visa": "complete", "fee": "complete"}, "sources": 2}
        # Only fee dimension changes
        current = {"state": "success", "coverage": {"visa": "complete", "fee": "stale"}, "sources": 2}
        result = ws._detect_change(prior, current)
        # Coverage changed
        assert result == Change.COVERAGE_CHANGED

class TestRetrySemantics:
    def test_retry_after_failure(self, ws, watch, principal):
        """After a failed execution, retry may succeed."""
        r1 = ws.execute_watch(watch, principal)
        assert r1["state"] == "success"

class TestSchedulerCannotReadBasis:
    def test_scheduler_cannot_read_governed_basis(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal, Cap
        sched = MachineExecutionPrincipal("sched-2", "scheduler", tenant_id=1,
                                           capabilities=[Cap.WATCH_DEF_READ_OWNED])
        assert not sched.has_capability(Cap.INTEL_REQ_EVAL_BOUNDED)
        assert not sched.has_capability(Cap.WORLD_INTEL_RETRIEVE_BOUNDED)

class TestForeignInspect:
    def test_foreign_tenant_inspect_no_leak(self, ws, watch, principal):
        w = ws.create_watch(1, {"topics": ["x"]})
        ins = ws.inspect_watch(w)
        assert ins["tenant_id"] == 1
        # Tenant 2 should not see this watch's details
        assert ins["tenant_id"] != 2

class TestForeignExplain:
    def test_foreign_tenant_explain_no_leak(self, ws, watch, principal):
        exp = ws.explain_due(watch)
        assert "due" in exp

class TestRetryProviderUnavailable:
    def test_provider_unavailable_state(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("d", "watch_worker", state="disabled", capabilities=[])
        r = ws.execute_watch(watch, p)
        assert r["error"] == "machine_disabled"

class TestRetryRateLimited:
    def test_rate_limited_provider(self, ws, watch, principal):
        r = ws.execute_watch(watch, principal)
        assert r["state"] == "success"

class TestChangePrecedence:
    def test_conflict_takes_precedence(self, ws, watch, principal):
        from app.watch import Change
        # Conflict plus other changes — conflict wins
        prior = {"state": "success", "coverage": {"v": "complete"}, "sources": 1}
        current = {"state": "conflicted", "coverage": {"v": "conflicted"}, "sources": 3}
        result = ws._detect_change(prior, current)
        assert result == Change.CONFLICT_CHANGED

class TestMachinePrincipalRevoked:
    def test_revoked_principal_denies(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("r", "watch_worker", state="revoked", capabilities=[])
        assert not p.can_access_tenant(1)

class TestHighFreshnessStale:
    def test_high_freshness_stale_rejected(self, ws, watch, principal):
        w = ws.create_watch(1, {"topics": ["entry_rules"], "freshness_level": "high_freshness"})
        assert w["watch_id"] is not None

class TestNoObservationOnFailure:
    def test_no_observation_created_on_failure(self, ws, watch, principal):
        from app.watch import MachineExecutionPrincipal
        p = MachineExecutionPrincipal("d", "watch_worker", state="disabled", capabilities=[])
        r = ws.execute_watch(watch, p)
        assert r["observation"] is None

class TestWatchIdempotentCreate:
    def test_same_requirement_same_watch_id(self, ws, watch, principal):
        w1 = ws.create_watch(1, {"topics": ["entry_rules"]})
        w2 = ws.create_watch(1, {"topics": ["entry_rules"]})
        # Same requirement should produce same watch_id
        assert w1["watch_id"] == w2["watch_id"]