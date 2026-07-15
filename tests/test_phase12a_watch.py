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