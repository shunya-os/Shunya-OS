"""
SHUNYA Runtime Kernel — Canonical Runtime for the SHUNYA OS.

The RuntimeKernel manages the lifecycle of all engines: registration,
initialization, dependency resolution, event dispatch, health monitoring,
and graceful shutdown.

Usage:
    from core.runtime import RuntimeKernel, RuntimeConfig, Engine

    class MyEngine(Engine):
        engine_id = "my_engine"
        engine_type = "custom"
        def initialize(self): ...
        def shutdown(self): ...
        def health_check(self): ...
        def handle_event(self, event): ...
        def get_capabilities(self): return ["custom"]

    kernel = RuntimeKernel(RuntimeConfig.from_env())
    kernel.register_engine("my_engine", MyEngine())
    kernel.initialize()
    status = kernel.health_check()
    kernel.shutdown()
"""

from .engine import DependencyGraph, RuntimeKernel
from .models import (
    ConfigSource,
    CoreConfig,
    Engine,
    EngineStatus,
    EventConfig,
    HealthCheckResult,
    HealthLevel,
    HealthStatus,
    IdentityConfig,
    RuntimeConfig,
)

__all__ = [
    # Core engine interface
    "Engine",
    "EngineStatus",
    # Configuration
    "RuntimeConfig",
    "CoreConfig",
    "IdentityConfig",
    "EventConfig",
    "ConfigSource",
    # Health
    "HealthStatus",
    "HealthLevel",
    "HealthCheckResult",
    # Kernel
    "RuntimeKernel",
    "DependencyGraph",
]
