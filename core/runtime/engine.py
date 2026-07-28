"""
SHUNYA Runtime Kernel — Dependency Graph and Runtime Kernel

The RuntimeKernel manages the lifecycle of all engines: registration,
initialization, health monitoring, event dispatch, and shutdown.
The DependencyGraph validates module ordering and detects circular
dependencies.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from .models import (
    Engine,
    EngineStatus,
    HealthCheckResult,
    HealthLevel,
    HealthStatus,
    RuntimeConfig,
)

# =========================================================================
# Dependency Graph
# =========================================================================


class DependencyGraph:
    """Directed acyclic graph (DAG) of engine/module dependencies.

    Tracks which engines depend on which other engines, validates that
    no circular dependencies exist, and computes the correct startup
    and shutdown order via topological sort.

    Usage:
        graph = DependencyGraph()
        graph.add_node("engine_a", depends_on=["engine_b"])
        graph.add_node("engine_b")
        order = graph.startup_order()  # ["engine_b", "engine_a"]
    """

    def __init__(self) -> None:
        # Adjacency list: node → list of node ids it depends on
        self._dependencies: dict[str, list[str]] = {}
        # Reverse index: node → list of nodes that depend on it
        self._dependents: dict[str, list[str]] = defaultdict(list)

    def add_node(self, node_id: str, depends_on: list[str] | None = None) -> None:
        """Register a node with optional dependency list.

        Args:
            node_id: Unique identifier for the node (e.g. engine_id).
            depends_on: List of node_ids that this node depends on.
                        Empty list means no dependencies.

        Raises:
            ValueError: If node_id references itself in depends_on.
        """
        deps = depends_on or []
        if node_id in deps:
            raise ValueError(
                f"Node '{node_id}' cannot depend on itself."
            )
        self._dependencies[node_id] = list(deps)
        for dep in deps:
            self._dependents[dep].append(node_id)

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the graph.

        Also removes edges referencing this node from other nodes'
        dependency lists.

        Args:
            node_id: Node to remove.

        Raises:
            KeyError: If node_id is not registered.
        """
        if node_id not in self._dependencies:
            raise KeyError(f"Node '{node_id}' is not registered in the dependency graph.")

        # Remove from dependents lists of its dependencies
        for dep in self._dependencies[node_id]:
            if node_id in self._dependents.get(dep, []):
                self._dependents[dep].remove(node_id)

        # Remove from other nodes' dependency lists
        for other_id, other_deps in self._dependencies.items():
            if node_id in other_deps:
                other_deps.remove(node_id)

        # Clean up
        del self._dependencies[node_id]
        self._dependents.pop(node_id, None)

    def get_dependencies(self, node_id: str) -> list[str]:
        """Return the list of nodes that *node_id* depends on."""
        return list(self._dependencies.get(node_id, []))

    def get_dependents(self, node_id: str) -> list[str]:
        """Return the list of nodes that depend on *node_id*."""
        return list(self._dependents.get(node_id, []))

    def has_node(self, node_id: str) -> bool:
        """Check whether a node is registered."""
        return node_id in self._dependencies

    @property
    def node_count(self) -> int:
        """Number of registered nodes."""
        return len(self._dependencies)

    @property
    def edge_count(self) -> int:
        """Number of dependency edges."""
        return sum(len(deps) for deps in self._dependencies.values())

    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles in the dependency graph.

        Uses DFS-based cycle detection. Returns a list of cycles,
        where each cycle is a list of node_ids forming a cycle.

        Returns:
            List of cycles. Empty list means the graph is acyclic.
        """
        visited: set[str] = set()
        in_stack: set[str] = set()
        cycles: list[list[str]] = []
        parent: dict[str, str | None] = {}

        def _dfs(node: str) -> None:
            visited.add(node)
            in_stack.add(node)
            for dep in self._dependencies.get(node, []):
                if dep not in visited:
                    parent[dep] = node
                    _dfs(dep)
                elif dep in in_stack:
                    # Reconstruct the cycle
                    cycle: list[str] = [dep, node]
                    cur = node
                    while cur != dep and parent.get(cur) is not None:
                        cur = parent[cur]  # type: ignore[assignment]
                        if cur != dep:
                            cycle.append(cur)
                    cycle.reverse()
                    cycles.append(cycle)
            in_stack.discard(node)

        for nid in list(self._dependencies.keys()):
            if nid not in visited:
                _dfs(nid)

        return cycles

    def validate(self) -> None:
        """Validate the graph has no circular dependencies.

        Raises:
            ValueError: If one or more cycles are detected.
        """
        cycles = self.detect_cycles()
        if cycles:
            cycle_strs = [" → ".join(c) for c in cycles]
            raise ValueError(
                f"Circular dependencies detected ({len(cycles)} cycle(s)):\n"
                + "\n".join(f"  {s}" for s in cycle_strs)
            )

    def startup_order(self) -> list[str]:
        """Return nodes in dependency-satisfied startup order.

        Dependencies come first. Uses Kahn's algorithm (topological sort).

        Returns:
            List of node_ids in startup order.

        Raises:
            ValueError: If the graph contains cycles.
        """
        # Build in-degree count
        in_degree: dict[str, int] = {}
        for nid in self._dependencies:
            in_degree.setdefault(nid, 0)
        for nid, deps in self._dependencies.items():
            for dep in deps:
                in_degree.setdefault(dep, 0)
                if nid in in_degree:
                    in_degree[nid] += 1

        # Nodes with zero in-degree (no unsatisfied dependencies)
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for dependent in self._dependents.get(node, []):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        if len(order) != len(self._dependencies):
            raise ValueError(
                f"Topological sort failed: graph has {len(self._dependencies)} nodes "
                f"but only {len(order)} could be ordered (cycle detected)."
            )

        return order

    def shutdown_order(self) -> list[str]:
        """Return nodes in reverse-startup (safest shutdown) order.

        Dependents shut down before their dependencies.
        """
        return list(reversed(self.startup_order()))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the dependency graph for diagnostics."""
        return {
            "nodes": sorted(self._dependencies.keys()),
            "dependencies": {
                nid: list(deps) for nid, deps in sorted(self._dependencies.items())
            },
            "dependents": {
                nid: sorted(deps) for nid, deps in sorted(self._dependents.items())
            },
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "cycles": self.detect_cycles(),
        }


# =========================================================================
# Runtime Kernel
# =========================================================================


class RuntimeKernel:
    """Canonical runtime kernel that manages engine lifecycle.

    Responsibilities:
    - Engine registration, initialization, and shutdown
    - Dependency validation and startup ordering via DependencyGraph
    - Event dispatch to all registered engines
    - Runtime health monitoring (health_check, diagnostics)
    - Type-safe configuration management

    This is a concrete class that composes with the Engine interface.
    It does NOT auto-initialize on import; call initialize() explicitly.

    Usage:
        kernel = RuntimeKernel()
        kernel.register_engine("evt", EventEngine())
        kernel.initialize()
        kernel.dispatch_event("ping", {"ts": 123})
        status = kernel.health_check()
        kernel.shutdown()
    """

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self._config: RuntimeConfig = config or RuntimeConfig()
        self._config.validate()

        self._engines: dict[str, Engine] = {}
        self._dependency_graph = DependencyGraph()
        self._event_handlers: dict[str, list[Callable[[Any], None]]] = {}
        self._started_at: float | None = None
        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> RuntimeConfig:
        """Current runtime configuration."""
        return self._config

    @property
    def engines(self) -> dict[str, Engine]:
        """All registered engines keyed by engine_id."""
        return dict(self._engines)

    @property
    def dependency_graph(self) -> DependencyGraph:
        """Dependency graph used for startup ordering."""
        return self._dependency_graph

    @property
    def initialized(self) -> bool:
        """Whether the runtime has been initialized."""
        return self._initialized

    @property
    def uptime_seconds(self) -> float:
        """Seconds since initialize() was called, or 0.0."""
        if self._started_at is None:
            return 0.0
        return time.time() - self._started_at

    # ------------------------------------------------------------------
    # Engine Registration & Management
    # ------------------------------------------------------------------

    def register_engine(
        self,
        engine_id: str,
        engine: Engine,
        depends_on: list[str] | None = None,
    ) -> None:
        """Register an engine with the runtime.

        Args:
            engine_id: Unique identifier for this engine instance.
            engine: An Engine instance.
            depends_on: List of engine_ids that this engine depends on.

        Raises:
            ValueError: If engine_id is already registered.
            TypeError: If engine does not implement the Engine interface.
        """
        if not isinstance(engine, Engine):
            raise TypeError(
                f"Engine must implement the Engine interface (ABC). "
                f"Got {type(engine).__name__}"
            )
        if engine_id in self._engines:
            raise ValueError(
                f"Engine '{engine_id}' is already registered."
            )

        if not engine.engine_id:
            engine.engine_id = engine_id
        if not engine.engine_type:
            engine.engine_type = engine_id

        self._engines[engine_id] = engine
        self._dependency_graph.add_node(engine_id, depends_on=depends_on or [])

    def unregister_engine(self, engine_id: str) -> None:
        """Unregister an engine from the runtime.

        If the engine is currently running, it is shut down first.

        Args:
            engine_id: Engine to unregister.

        Raises:
            KeyError: If engine_id is not registered.
        """
        if engine_id not in self._engines:
            raise KeyError(f"Engine '{engine_id}' is not registered.")

        engine = self._engines[engine_id]
        if engine.status != EngineStatus.OFFLINE:
            engine.shutdown()
            engine._status = EngineStatus.OFFLINE  # type: ignore[attr-defined]

        del self._engines[engine_id]
        self._dependency_graph.remove_node(engine_id)
        self._event_handlers.pop(engine_id, None)

    def get_engine(self, engine_id: str) -> Engine | None:
        """Look up a registered engine by id.

        Returns None if not found (use has_engine for boolean check).
        """
        return self._engines.get(engine_id)

    def has_engine(self, engine_id: str) -> bool:
        """Check if an engine is registered."""
        return engine_id in self._engines

    def list_engines(self) -> list[dict[str, str]]:
        """List all registered engines with their id, type, and status."""
        return [
            {
                "engine_id": eid,
                "engine_type": eng.engine_type,
                "status": eng.status.value,
            }
            for eid, eng in sorted(self._engines.items())
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize all registered engines in dependency order.

        Validates the dependency graph, then calls initialize() on each
        engine following startup_order(). Engines that fail are marked
        as degraded but do not block other engines.

        Raises:
            RuntimeError: If no engines are registered.
            ValueError: If the dependency graph has cycles.
        """
        if not self._engines:
            raise RuntimeError(
                "Cannot initialize runtime: no engines registered."
            )

        self._dependency_graph.validate()
        order = self._dependency_graph.startup_order()
        self._started_at = time.time()

        failed: list[str] = []
        for engine_id in order:
            engine = self._engines[engine_id]
            try:
                engine.initialize()
                engine._status = EngineStatus.ACTIVE  # type: ignore[attr-defined]
            except Exception as exc:
                engine._status = EngineStatus.DEGRADED  # type: ignore[attr-defined]
                failed.append(f"{engine_id}: {exc}")

        self._initialized = True
        self.dispatch_event("runtime.initialized", {"order": order, "failed": failed})

        if failed:
            raise RuntimeError(
                f"Runtime initialized with {len(failed)} engine failure(s):\n"
                + "\n".join(f"  {f}" for f in failed)
            )

    def shutdown(self) -> None:
        """Shut down all engines in reverse-dependency order.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if not self._initialized or not self._engines:
            return

        try:
            order = self._dependency_graph.shutdown_order()
        except ValueError:
            # Fall back to reverse-insertion order if graph is inconsistent
            order = list(reversed(list(self._engines.keys())))

        exceptions: list[str] = []
        for engine_id in order:
            engine = self._engines.get(engine_id)
            if engine is None or engine.status == EngineStatus.OFFLINE:
                continue
            try:
                engine.shutdown()
                engine._status = EngineStatus.OFFLINE  # type: ignore[attr-defined]
            except Exception as exc:
                exceptions.append(f"{engine_id}: {exc}")

        self._initialized = False
        self._started_at = None

        if exceptions:
            raise RuntimeError(
                f"Shutdown completed with {len(exceptions)} error(s):\n"
                + "\n".join(f"  {e}" for e in exceptions)
            )

    # ------------------------------------------------------------------
    # Event Dispatch
    # ------------------------------------------------------------------

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[Any], None],
        handler_name: str | None = None,
    ) -> None:
        """Register a callable as a handler for a specific event type.

        Args:
            event_type: Event type string (e.g. 'runtime.initialized').
            handler: Callable accepting a single event payload argument.
            handler_name: Optional identifier for diagnostics.

        Raises:
            ValueError: If max_handlers_per_event would be exceeded.
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        if (
            len(self._event_handlers[event_type])
            >= self._config.event.max_handlers_per_event
        ):
            raise ValueError(
                f"Max handlers ({self._config.event.max_handlers_per_event}) "
                f"reached for event type '{event_type}'."
            )
        self._event_handlers[event_type].append(handler)

    def unregister_event_handler(
        self,
        event_type: str,
        handler: Callable[[Any], None],
    ) -> bool:
        """Remove a previously registered event handler.

        Returns True if the handler was removed, False if not found.
        """
        handlers = self._event_handlers.get(event_type, [])
        try:
            handlers.remove(handler)
            return True
        except ValueError:
            return False

    def dispatch_event(self, event_type: str, payload: Any = None) -> None:
        """Dispatch an event to all registered handlers for that type.

        The event is also forwarded to every engine's handle_event method
        so engines can react globally if needed.

        Args:
            event_type: Event type string.
            payload: Event payload (any serializable value).
        """
        if not self._event_handlers and not self._engines:
            return

        # Dispatch to direct handlers
        for handler in list(self._event_handlers.get(event_type, [])):
            try:
                handler(payload)
            except Exception:
                pass  # handlers must not crash the dispatch loop

        # Forward to all engines
        for engine in self._engines.values():
            if engine.status == EngineStatus.ACTIVE:
                try:
                    engine.handle_event(
                        {"type": event_type, "payload": payload}
                    )
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Health & Diagnostics
    # ------------------------------------------------------------------

    def health_check(self) -> HealthStatus:
        """Aggregate health of all registered engines.

        Collects each engine's health_check(), derives the aggregate
        health level, and returns a HealthStatus snapshot.

        Returns:
            HealthStatus with per-engine statuses, named checks, and uptime.
        """
        if not self._initialized:
            return HealthStatus(
                status=HealthLevel.UNHEALTHY,
                version=self._config.core.version,
                uptime_seconds=0.0,
                engines={},
                checks={"runtime_initialized": False},
            )

        eng_statuses: dict[str, str] = {}
        all_checks: dict[str, bool] = {"runtime_initialized": True}
        all_check_details: list[HealthCheckResult] = []
        degraded_count = 0
        offline_count = 0

        for eid, engine in sorted(self._engines.items()):
            eng_statuses[eid] = engine.status.value

            if engine.status == EngineStatus.OFFLINE:
                offline_count += 1
                continue

            try:
                hs = engine.health_check()
                for check_name, passed in hs.checks.items():
                    full_name = f"{eid}.{check_name}"
                    all_checks[full_name] = passed
                for detail in hs.check_results:
                    all_check_details.append(detail)
                if hs.status == HealthLevel.DEGRADED or hs.status == HealthLevel.UNHEALTHY:
                    degraded_count += 1
            except Exception:
                all_checks[f"{eid}.health_check"] = False
                all_check_details.append(
                    HealthCheckResult(
                        name=f"{eid}.health_check",
                        passed=False,
                        message="health_check() raised an exception",
                    )
                )
                degraded_count += 1

        # Derive aggregate health level
        if offline_count == len(self._engines):
            aggregate = HealthLevel.UNHEALTHY
        elif any(not v for v in all_checks.values()) or degraded_count > 0:
            aggregate = HealthLevel.DEGRADED
        else:
            aggregate = HealthLevel.HEALTHY

        return HealthStatus(
            status=aggregate,
            engines=eng_statuses,
            uptime_seconds=self.uptime_seconds,
            version=self._config.core.version,
            checks=all_checks,
            check_results=all_check_details,
            started_at=(
                datetime.fromtimestamp(self._started_at, tz=timezone.utc).isoformat()
                if self._started_at
                else None
            ),
        )

    def diagnostics(self) -> dict[str, Any]:
        """Return detailed subsystem state for debugging.

        Includes engine counts, status distribution, event handler
        counts, dependency graph, timing, and configuration summary.

        Returns:
            Dict with full diagnostic information.
        """
        status_counts: dict[str, int] = defaultdict(int)
        for engine in self._engines.values():
            status_counts[engine.status.value] += 1

        handler_counts: dict[str, int] = {
            etype: len(handlers)
            for etype, handlers in sorted(self._event_handlers.items())
        }

        return {
            "initialized": self._initialized,
            "uptime_seconds": self.uptime_seconds,
            "version": self._config.core.version,
            "environment": self._config.core.environment,
            "engine_count": len(self._engines),
            "engines_by_status": dict(status_counts),
            "handler_count": sum(handler_counts.values()),
            "handlers_by_type": handler_counts,
            "dependency_graph": self._dependency_graph.to_dict(),
            "config": self._config.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }