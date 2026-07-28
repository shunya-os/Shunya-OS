"""
SHUNYA Runtime Kernel — Domain Models

Defines the canonical data types for the runtime kernel:
Engine interface, RuntimeConfig, and HealthStatus.

Every runtime-managed component (engine, module, adapter) implements
the Engine interface. The runtime uses these models for configuration
loading, health reporting, and lifecycle management.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# =========================================================================
# Enums
# =========================================================================


class EngineStatus(StrEnum):
    """Operational status of a registered engine."""

    ACTIVE = "active"
    """Engine is fully operational and processing requests."""

    PAUSED = "paused"
    """Engine is temporarily suspended; no new work accepted."""

    DEGRADED = "degraded"
    """Engine is operational but with reduced capacity or non-critical failures."""

    OFFLINE = "offline"
    """Engine is not running; initialization has not been called."""


class HealthLevel(StrEnum):
    """Aggregate health level for the runtime or an individual engine."""

    HEALTHY = "healthy"
    """All checks pass; the component is fully operational."""

    DEGRADED = "degraded"
    """Some non-critical checks fail; the component still serves requests."""

    UNHEALTHY = "unhealthy"
    """Critical checks fail; the component cannot serve requests."""


class ConfigSource(StrEnum):
    """Origin of a configuration value."""

    DEFAULT = "default"
    """The value came from a compiled-in default."""

    DICT = "dict"
    """The value came from a dictionary passed at runtime."""

    ENV = "env"
    """The value came from an environment variable override."""

    FILE = "file"
    """The value came from a configuration file."""


# =========================================================================
# Health Status
# =========================================================================


@dataclass
class HealthCheckResult:
    """Result of a single named health check."""

    name: str
    """Human-readable identifier for the check (e.g. 'db_connectivity')."""

    passed: bool
    """Whether the check succeeded."""

    message: str = ""
    """Optional human-readable detail when the check fails."""


@dataclass
class HealthStatus:
    """Aggregate health snapshot of the runtime or a single engine.

    Carries per-engine status dict, a list of named checks, uptime,
    and version information.
    """

    status: HealthLevel = HealthLevel.HEALTHY
    """Aggregate health level derived from all checks."""

    engines: dict[str, str] = field(default_factory=dict)
    """Per-engine status keyed by engine_id (values are EngineStatus values)."""

    uptime_seconds: float = 0.0
    """Number of seconds since the runtime was initialized."""

    version: str = "0.0.0"
    """Runtime version string."""

    checks: dict[str, bool] = field(default_factory=dict)
    """Named health checks: check name → passed (True/False)."""

    check_results: list[HealthCheckResult] = field(default_factory=list)
    """Detailed health check results with messages."""

    started_at: str | None = None
    """ISO-8601 timestamp of when the runtime was initialized."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON responses."""
        return {
            "status": self.status.value,
            "engines": dict(self.engines),
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "checks": dict(self.checks),
            "check_results": [
                {"name": r.name, "passed": r.passed, "message": r.message}
                for r in self.check_results
            ],
            "started_at": self.started_at or "",
        }

    @property
    def is_healthy(self) -> bool:
        """Convenience: True when every check passed and no engines are offline."""
        if self.status == HealthLevel.UNHEALTHY:
            return False
        if any(v == EngineStatus.OFFLINE for v in self.engines.values()):
            return False
        return all(self.checks.values()) if self.checks else True


# =========================================================================
# Runtime Configuration
# =========================================================================


@dataclass
class CoreConfig:
    """Configuration for the core runtime behaviour."""

    name: str = "shunya"
    """Name of this runtime instance."""

    version: str = "0.1.0"
    """Runtime version string."""

    environment: str = "development"
    """Deployment environment: development, staging, or production."""

    debug: bool = False
    """Enable debug-level logging and diagnostics."""

    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""

    def validate(self) -> None:
        """Validate configuration values.

        Raises ValueError if any values are invalid.
        """
        valid_envs = {"development", "staging", "production"}
        if self.environment not in valid_envs:
            raise ValueError(
                f"Invalid environment '{self.environment}'. "
                f"Must be one of {sorted(valid_envs)}."
            )
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log_level '{self.log_level}'. "
                f"Must be one of {sorted(valid_levels)}."
            )


@dataclass
class IdentityConfig:
    """Configuration for the identity / authentication subsystem."""

    provider: str = "internal"
    """Identity provider identifier (internal, oauth, ldap, etc.)."""

    token_expiry_seconds: int = 3600
    """Default token lifetime in seconds."""

    max_failed_attempts: int = 5
    """Lockout threshold for failed authentication attempts."""

    def validate(self) -> None:
        """Validate identity config values."""
        if self.token_expiry_seconds < 60:
            raise ValueError(
                f"token_expiry_seconds must be >= 60, got {self.token_expiry_seconds}"
            )
        if self.max_failed_attempts < 1:
            raise ValueError(
                f"max_failed_attempts must be >= 1, got {self.max_failed_attempts}"
            )


@dataclass
class EventConfig:
    """Configuration for the event dispatch subsystem."""

    max_queue_size: int = 10_000
    """Maximum number of queued events before back-pressure applies."""

    async_dispatch: bool = True
    """Dispatch events asynchronously when True, synchronously when False."""

    max_handlers_per_event: int = 50
    """Maximum number of registered handlers per event type."""

    def validate(self) -> None:
        """Validate event config values."""
        if self.max_queue_size < 100:
            raise ValueError(
                f"max_queue_size must be >= 100, got {self.max_queue_size}"
            )
        if self.max_handlers_per_event < 1:
            raise ValueError(
                f"max_handlers_per_event must be >= 1, got {self.max_handlers_per_event}"
            )


@dataclass
class RuntimeConfig:
    """Type-safe top-level runtime configuration.

    Supports nested config sections (core, identity, event), environment
    variable overrides with SHUNYA_ prefix, and validation on load.

    Usage:
        config = RuntimeConfig()
        config = RuntimeConfig.from_dict({"core": {"debug": True}})
        config = RuntimeConfig.from_env()  # reads SHUNYA_* env vars
    """

    core: CoreConfig = field(default_factory=CoreConfig)
    identity: IdentityConfig = field(default_factory=IdentityConfig)
    event: EventConfig = field(default_factory=EventConfig)

    # Allow arbitrary engine-specific config sections
    engines: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Engine-specific configuration keyed by engine_id."""

    def validate(self) -> None:
        """Validate all nested configuration sections.

        Raises ValueError on first invalid value.
        """
        self.core.validate()
        self.identity.validate()
        self.event.validate()

    def to_dict(self) -> dict[str, Any]:
        """Serialize full configuration to a nested dict."""
        return {
            "core": {
                "name": self.core.name,
                "version": self.core.version,
                "environment": self.core.environment,
                "debug": self.core.debug,
                "log_level": self.core.log_level,
            },
            "identity": {
                "provider": self.identity.provider,
                "token_expiry_seconds": self.identity.token_expiry_seconds,
                "max_failed_attempts": self.identity.max_failed_attempts,
            },
            "event": {
                "max_queue_size": self.event.max_queue_size,
                "async_dispatch": self.event.async_dispatch,
                "max_handlers_per_event": self.event.max_handlers_per_event,
            },
            "engines": dict(self.engines),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeConfig:
        """Create a config from a nested dict, overriding defaults.

        Only supplied keys are overridden; unspecified keys keep defaults.
        """
        instance = cls()

        core_data = data.get("core", {})
        if isinstance(core_data, dict):
            instance.core = CoreConfig(
                name=core_data.get("name", instance.core.name),
                version=core_data.get("version", instance.core.version),
                environment=core_data.get("environment", instance.core.environment),
                debug=core_data.get("debug", instance.core.debug),
                log_level=core_data.get("log_level", instance.core.log_level),
            )

        identity_data = data.get("identity", {})
        if isinstance(identity_data, dict):
            instance.identity = IdentityConfig(
                provider=identity_data.get("provider", instance.identity.provider),
                token_expiry_seconds=identity_data.get(
                    "token_expiry_seconds", instance.identity.token_expiry_seconds
                ),
                max_failed_attempts=identity_data.get(
                    "max_failed_attempts", instance.identity.max_failed_attempts
                ),
            )

        event_data = data.get("event", {})
        if isinstance(event_data, dict):
            instance.event = EventConfig(
                max_queue_size=event_data.get(
                    "max_queue_size", instance.event.max_queue_size
                ),
                async_dispatch=event_data.get(
                    "async_dispatch", instance.event.async_dispatch
                ),
                max_handlers_per_event=event_data.get(
                    "max_handlers_per_event", instance.event.max_handlers_per_event
                ),
            )

        engines_data = data.get("engines", {})
        if isinstance(engines_data, dict):
            instance.engines = {
                k: dict(v) for k, v in engines_data.items()
            }

        return instance

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        """Create a config by reading SHUNYA_* environment variables.

        Mapping:
            SHUNYA_CORE_NAME          → core.name
            SHUNYA_CORE_VERSION       → core.version
            SHUNYA_CORE_ENVIRONMENT   → core.environment
            SHUNYA_CORE_DEBUG         → core.debug
            SHUNYA_CORE_LOG_LEVEL     → core.log_level
            SHUNYA_IDENTITY_PROVIDER  → identity.provider
            SHUNYA_EVENT_MAX_QUEUE    → event.max_queue_size
            SHUNYA_EVENT_ASYNC        → event.async_dispatch
        """
        instance = cls()

        if v := os.environ.get("SHUNYA_CORE_NAME"):
            instance.core.name = v
        if v := os.environ.get("SHUNYA_CORE_VERSION"):
            instance.core.version = v
        if v := os.environ.get("SHUNYA_CORE_ENVIRONMENT"):
            instance.core.environment = v
        if v := os.environ.get("SHUNYA_CORE_DEBUG"):
            instance.core.debug = v.lower() in ("1", "true", "yes")
        if v := os.environ.get("SHUNYA_CORE_LOG_LEVEL"):
            instance.core.log_level = v.upper()
        if v := os.environ.get("SHUNYA_IDENTITY_PROVIDER"):
            instance.identity.provider = v
        if v := os.environ.get("SHUNYA_EVENT_MAX_QUEUE"):
            instance.event.max_queue_size = int(v)
        if v := os.environ.get("SHUNYA_EVENT_ASYNC"):
            instance.event.async_dispatch = v.lower() in ("1", "true", "yes")

        return instance

    @classmethod
    def from_file(cls, path: str) -> RuntimeConfig:
        """Load configuration from a JSON or YAML file.

        Supports .json and .yaml/.yml extensions. The file is read and
        passed to from_dict().

        Raises FileNotFoundError if the file does not exist.
        Raises ValueError for unsupported file extensions.
        """
        import json

        if not os.path.isfile(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        ext = os.path.splitext(path)[1].lower()

        if ext == ".json":
            with open(path, "r") as f:
                data = json.load(f)
        elif ext in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore[import-untyped]
            except ImportError:
                raise ImportError(
                    "PyYAML is required to load .yaml configuration files. "
                    "Install with: pip install pyyaml"
                )
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(
                f"Unsupported configuration file extension '{ext}'. "
                f"Supported: .json, .yaml, .yml"
            )

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuration file must contain a top-level dict, got {type(data).__name__}"
            )

        return cls.from_dict(data)


# =========================================================================
# Engine Interface
# =========================================================================


class Engine(ABC):
    """Abstract interface for every engine managed by the runtime kernel.

    All sub-engines, modules, and adapters implement this interface.
    The RuntimeKernel discovers, initialises, monitors, and shuts down
    engines through these methods.

    Subclasses must set engine_id and engine_type as class attributes
    (or override the properties) and implement all abstract methods.
    """

    engine_id: str = ""
    """Unique identifier for this engine instance within the runtime."""

    engine_type: str = ""
    """Logical type string for categorisation (e.g. 'event', 'identity')."""

    def __init__(self) -> None:
        self._status: EngineStatus = EngineStatus.OFFLINE

    @property
    def status(self) -> EngineStatus:
        """Current operational status."""
        return self._status

    @abstractmethod
    def initialize(self) -> None:
        """Initialise the engine.

        Called by RuntimeKernel during startup. Engines should allocate
        resources, open connections, and register event handlers here.

        Raises RuntimeError on initialisation failure.
        """
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shut down the engine.

        Called by RuntimeKernel during teardown. Engines should release
        resources, close connections, and flush pending work.
        """
        ...

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Return the current health snapshot of this engine.

        Must be safe to call at any time (no side effects).
        """
        ...

    @abstractmethod
    def handle_event(self, event: Any) -> None:
        """Process a runtime event dispatched by the kernel.

        Args:
            event: The event payload. The type and shape are determined
                   by the event dispatch contract.
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return a list of capability identifiers this engine provides.

        Capabilities are used by the runtime for dependency resolution
        and capability-based discovery.
        """
        ...