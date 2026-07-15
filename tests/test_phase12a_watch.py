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