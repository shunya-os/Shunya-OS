"""SHUNYA OS Kernel — the single bootstrap that wires all core runtimes.

The OS Kernel:
  1. Initializes all core runtimes in dependency order
  2. Registers each runtime with the canonical pipeline
  3. Provides system-wide health check
  4. Provides a single process_intent() entry point
  5. Exposes each runtime for direct access by adapters

No subsystem may bypass the OS Kernel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .runtime_pipeline import (
    PipelineContext,
    PipelineStage,
    RuntimeInterface,
    RuntimePipeline,
)

# ---------------------------------------------------------------------------
# Mock runtimes — used during convergence as adapters until each real runtime
# is wired. Each mock implements RuntimeInterface and returns noop/completed.
# ---------------------------------------------------------------------------


@dataclass
class MockRuntime(RuntimeInterface):
    """A mock runtime that completes every stage as noop.

    Used during progressive convergence. When the real runtime is wired,
    the mock is replaced.
    """

    name: str = ""
    stages: list[PipelineStage] = field(default_factory=list)
    _status: str = "healthy"

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        return {"status": "noop", "runtime": self.name, "stage": stage.value}

    def health_check(self) -> dict[str, Any]:
        return {"status": self._status, "runtime": self.name}


# ---------------------------------------------------------------------------
# OS Kernel
# ---------------------------------------------------------------------------


_SHUNYA_OS: ShunyaOS | None = None


class ShunyaOS:
    """The SHUNYA Operating System Kernel.

    Usage:
        os = ShunyaOS()
        os.bootstrap()          # initialize all runtimes
        result = os.process_intent("talk_to_customer", {"name": "Alice"})
        os.health_check()       # aggregate health
        os.shutdown()           # graceful shutdown
    """

    def __init__(self) -> None:
        self._pipeline = RuntimePipeline()
        self._runtimes: dict[str, RuntimeInterface] = {}
        self._bootstrapped = False

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def bootstrap(self) -> None:
        """Initialize all core runtimes and register with the pipeline.

        During convergence (Phase L), this creates mock runtimes for all
        stages. As each real runtime is integrated, the mock is replaced.
        """
        if self._bootstrapped:
            return

        from core.kernel_runtime import KernelRuntime
        self._kernel_runtime = KernelRuntime()
        self._runtimes["kernel"] = self._kernel_runtime
        self._pipeline.register(self._kernel_runtime)

        from core.identity_runtime import IdentityRuntime
        self._identity_runtime = IdentityRuntime()
        self._runtimes["identity"] = self._identity_runtime
        self._pipeline.register(self._identity_runtime)

        from core.runtime_pipeline.adapters import (
            AutomationRuntimeAdapter,
            CognitiveRuntimeAdapter,
            ExecutionRuntimeAdapter,
            MemoryKnowledgeRuntimeAdapter,
            PlanningRuntimeAdapter,
            WorkspaceRuntimeAdapter,
        )

        # Memory & Knowledge — replaces knowledge_graph and memory mocks
        self._memory_knowledge_runtime = MemoryKnowledgeRuntimeAdapter()
        self._runtimes["memory_knowledge"] = self._memory_knowledge_runtime
        self._pipeline.register(self._memory_knowledge_runtime)

        # Planning — replaces planning mock
        self._planning_runtime = PlanningRuntimeAdapter()
        self._runtimes["planning"] = self._planning_runtime
        self._pipeline.register(self._planning_runtime)

        # Cognitive (8 intelligence engines) — replaces reasoning mock
        self._cognitive_runtime = CognitiveRuntimeAdapter()
        self._runtimes["cognitive"] = self._cognitive_runtime
        self._pipeline.register(self._cognitive_runtime)

        # Execution — replaces execution mock
        self._execution_runtime = ExecutionRuntimeAdapter()
        self._runtimes["execution"] = self._execution_runtime
        self._pipeline.register(self._execution_runtime)

        # Automation — replaces automation mock
        self._automation_runtime = AutomationRuntimeAdapter()
        self._runtimes["automation"] = self._automation_runtime
        self._pipeline.register(self._automation_runtime)

        from core.runtime_pipeline.projection_adapter import ProjectionRuntimeAdapter
        self._projection_runtime = ProjectionRuntimeAdapter()
        self._runtimes["projection"] = self._projection_runtime
        self._pipeline.register(self._projection_runtime)

        # Workspace — replaces workspace mock
        self._workspace_runtime = WorkspaceRuntimeAdapter()
        self._runtimes["workspace"] = self._workspace_runtime
        self._pipeline.register(self._workspace_runtime)

        self._bootstrapped = True

    def _register_mock(self, name: str, stages: list[PipelineStage]) -> None:
        runtime = MockRuntime(name=name, stages=stages)
        self._runtimes[name] = runtime
        self._pipeline.register(runtime)

    # ------------------------------------------------------------------
    # Runtime replacement — swap a mock for a real runtime during convergence
    # ------------------------------------------------------------------

    def replace_runtime(self, name: str, runtime: RuntimeInterface) -> None:
        """Replace a mock runtime with a real implementation.

        Args:
            name: The runtime name (must match an existing mock).
            runtime: The real runtime instance.

        Raises ValueError if no runtime with that name is registered.
        """
        if name not in self._runtimes:
            raise ValueError(f"Runtime '{name}' is not registered. Cannot replace.")
        self._pipeline.unregister(name)
        self._runtimes[name] = runtime
        self._pipeline.register(runtime)

    def get_runtime(self, name: str) -> RuntimeInterface | None:
        """Get a registered runtime by name."""
        return self._runtimes.get(name)

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    def process_intent(
        self,
        intent: str,
        parameters: dict[str, Any] | None = None,
        identity_id: str | None = None,
        object_id: str | None = None,
    ) -> PipelineContext:
        """Process an intent through the canonical pipeline.

        This is the single entry point for all user actions in SHUNYA.
        Every route, webhook, API endpoint, and automation trigger must
        eventually call this method.

        Args:
            intent: The business intent string.
            parameters: Structured intent parameters.
            identity_id: Pre-resolved actor identity.
            object_id: Pre-resolved target object.

        Returns:
            A completed PipelineContext with full execution trace.
        """
        if not self._bootstrapped:
            self.bootstrap()
        return self._pipeline.execute(
            intent=intent,
            parameters=parameters,
            identity_id=identity_id,
            object_id=object_id,
        )

    # ------------------------------------------------------------------
    # System health
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Aggregate health of the entire OS."""
        if not self._bootstrapped:
            return {"status": "not_bootstrapped", "component": "shunya_os"}
        return {
            "status": "healthy",
            "component": "shunya_os",
            "bootstrapped": self._bootstrapped,
            "runtime_count": len(self._runtimes),
            "pipeline": self._pipeline.health_check(),
        }

    def shutdown(self) -> None:
        """Graceful shutdown. Currently a stub for future cleanup."""
        self._pipeline = RuntimePipeline()
        self._runtimes.clear()
        self._bootstrapped = False

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> RuntimePipeline:
        return self._pipeline

    @property
    def runtimes(self) -> dict[str, RuntimeInterface]:
        return dict(self._runtimes)


# ---------------------------------------------------------------------------
# Global singleton accessor
# ---------------------------------------------------------------------------


def get_os() -> ShunyaOS:
    """Get or create the SHUNYA OS singleton."""
    global _SHUNYA_OS
    if _SHUNYA_OS is None:
        _SHUNYA_OS = ShunyaOS()
    return _SHUNYA_OS


def reset_os() -> None:
    """Reset the OS singleton (for testing)."""
    global _SHUNYA_OS
    if _SHUNYA_OS is not None:
        _SHUNYA_OS.shutdown()
    _SHUNYA_OS = None


__all__ = [
    "MockRuntime",
    "ShunyaOS",
    "get_os",
    "reset_os",
]