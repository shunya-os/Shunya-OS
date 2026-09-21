"""Deterministic contract test for ToolExecutionLayer dispatch.

Guards the invariant that motivated the GJ-12 singleton investigation:

    registered action   -> dispatches to the correct handler   (status "success")
    unregistered action -> deterministically skipped            (status "skipped")
    repeated            -> identical result
    suite order changed -> identical result

The layer's own contract is proved on a FRESH, isolated instance so the result
cannot depend on the process-global singleton's wiring order (see the lifecycle
note in core/intelligence_runtime/execution.py). A separate assertion documents
the shared singleton's monotonic handler set without assuming any key is absent.
"""
from __future__ import annotations

from core.intelligence_runtime.execution import ToolExecutionLayer
from core.intelligence_runtime.types import ActionType, PlanStep


def _step(action: ActionType):
    return PlanStep(action=action, description="probe", parameters={"token": "abc"})


class TestIsolatedLayerContract:
    """Contract proof on a fresh layer — independent of suite order."""

    def test_registered_action_dispatches_to_correct_handler(self):
        layer = ToolExecutionLayer()
        seen: list = []

        def handler(params):
            seen.append(params.get("token"))
            return {"echo": params.get("token")}

        layer.register(ActionType.ANSWER.value, handler)
        result = layer.execute(_step(ActionType.ANSWER))

        assert result["status"] == "success"
        assert result["action"] == ActionType.ANSWER.value
        assert result["result"] == {"echo": "abc"}
        assert seen == ["abc"]

    def test_unregistered_action_is_skipped(self):
        layer = ToolExecutionLayer()
        result = layer.execute(_step(ActionType.ROUTE))
        assert result["status"] == "skipped"
        assert result["action"] == ActionType.ROUTE.value

    def test_repeated_execution_is_stable(self):
        layer = ToolExecutionLayer()
        statuses = {layer.execute(_step(ActionType.DEFER))["status"] for _ in range(5)}
        assert statuses == {"skipped"}

    def test_handler_exception_is_reported_not_skipped(self):
        """A registered handler that raises must return "error", never "skipped"
        — the two outcomes are distinct and must not be conflated."""
        layer = ToolExecutionLayer()

        def boom(params):
            raise RuntimeError("handler blew up")

        layer.register(ActionType.AUTOMATE.value, boom)
        result = layer.execute(_step(ActionType.AUTOMATE))
        assert result["status"] == "error"
        assert "handler blew up" in result["error"]

    def test_public_introspection_api(self):
        layer = ToolExecutionLayer()
        assert layer.registered_actions() == []
        assert layer.is_registered("anything") is False
        layer.register("zeta", lambda p: {})
        layer.register("alpha", lambda p: {})
        assert layer.registered_actions() == ["alpha", "zeta"]
        assert layer.is_registered("alpha") is True
        assert layer.is_registered("beta") is False


class TestSharedSingletonLifecycle:
    """Documents the shared singleton's monotonic handler set.

    Registration is process-global; we pin it by calling ensure_runtime()
    ourselves rather than assuming an earlier test did.
    """

    def test_execute_is_a_registered_base_action(self):
        from core.intelligence_runtime import get_runtime
        from core.intelligence_runtime.integration import ensure_runtime

        ensure_runtime()
        executor = get_runtime().executor

        # ensure_runtime wires the four base actions; "execute" is one of them.
        for key in ("answer", "clarify", "execute", "automate"):
            assert executor.is_registered(key), f"{key} must be wired by ensure_runtime"

    def test_unregistered_action_type_stays_skipped_on_singleton(self):
        """No code path registers "defer"/"route"; the singleton must skip them
        in every suite order."""
        from core.intelligence_runtime import get_runtime
        from core.intelligence_runtime.integration import ensure_runtime

        ensure_runtime()
        executor = get_runtime().executor
        assert executor.is_registered(ActionType.DEFER.value) is False
        assert executor.execute(_step(ActionType.DEFER))["status"] == "skipped"

    def test_reset_then_ensure_rewires_the_singleton(self, app):
        """Regression guard for the reset/re-wire invariant.

        reset_runtime() drops the singleton AND must clear the wiring guard, so
        that the next ensure_runtime() re-wires a FRESH singleton. Before the
        fix this was broken: the executor was cleared but the guard stayed set,
        leaving the runtime permanently unwired (order-dependent behaviour).

        Runs inside the ``app`` fixture because resetting the runtime clears the
        DB-backed memory repository, which needs an application context.
        """
        from core.intelligence_runtime import get_runtime, reset_runtime
        from core.intelligence_runtime.integration import ensure_runtime

        ensure_runtime()
        assert get_runtime().executor.is_registered("execute")

        reset_runtime()
        # Fresh singleton: unwired until ensure_runtime() runs again.
        assert get_runtime().executor.registered_actions() == []

        ensure_runtime()
        # Re-wired: base actions are back.
        assert get_runtime().executor.is_registered("execute")
        assert get_runtime().executor.is_registered("answer")
