"""SHUNYA — Configuration System.

Centralized YAML-based configuration loader with schema validation,
per-environment config files, and environment variable override support.

Architectural authority: INFR-002 (SHUNYA_IMPLEMENTATION_PROGRAM.md)
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ---- Configuration Schema ---------------------------------------------------

CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = {
    "app": {
        "name": {"type": str, "required": True, "default": "shunya"},
        "environment": {"type": str, "required": False, "default": "development"},
        "debug": {"type": bool, "required": False, "default": False},
    },
    "event_bus": {
        "max_queue_size": {"type": int, "required": False, "default": 10000},
        "consumer_timeout_ms": {"type": int, "required": False, "default": 5000},
        "idempotency_cache_ttl_hours": {"type": int, "required": False, "default": 24},
        "retry_max_attempts": {"type": int, "required": False, "default": 3},
        "retry_backoff_ms": {"type": list, "required": False, "default": [100, 500, 2000]},
        "dead_letter_queue_size": {"type": int, "required": False, "default": 1000},
        "health_check_interval_s": {"type": int, "required": False, "default": 30},
    },
    "credential_store": {
        "encryption_key_id": {"type": str, "required": False, "default": "key-1"},
        "audit_log_enabled": {"type": bool, "required": False, "default": True},
    },
    "knowledge": {
        "iks_enabled": {"type": bool, "required": False, "default": True},
        "knowledge_layer_fallback": {"type": bool, "required": False, "default": True},
    },
    "governance": {
        "policy_registry_path": {"type": str, "required": False, "default": "policies/"},
        "audit_log_enabled": {"type": bool, "required": False, "default": True},
    },
    "logging": {
        "level": {"type": str, "required": False, "default": "INFO"},
        "format": {"type": str, "required": False, "default": "json"},
        "output": {"type": str, "required": False, "default": "stdout"},
        "privacy_filter_enabled": {"type": bool, "required": False, "default": True},
    },
    "metrics": {
        "enabled": {"type": bool, "required": False, "default": True},
        "port": {"type": int, "required": False, "default": 8001},
        "path": {"type": str, "required": False, "default": "/metrics"},
    },
    "health": {
        "enabled": {"type": bool, "required": False, "default": True},
        "path": {"type": str, "required": False, "default": "/health"},
        "check_interval_s": {"type": int, "required": False, "default": 30},
    },
    "persistence": {
        "database_url": {"type": str, "required": False, "default": "sqlite:///:memory:"},
        "pool_size": {"type": int, "required": False, "default": 5},
        "pool_timeout_s": {"type": int, "required": False, "default": 30},
        "echo": {"type": bool, "required": False, "default": False},
        "migration_dir": {"type": str, "required": False, "default": "app/data/migrations/"},
    },
    "engines": {
        "identity": {"type": dict, "required": False, "default": {}},
        "knowledge": {"type": dict, "required": False, "default": {}},
        "context_fusion": {"type": dict, "required": False, "default": {}},
        "reasoning": {"type": dict, "required": False, "default": {}},
        "planner": {"type": dict, "required": False, "default": {}},
        "governance": {"type": dict, "required": False, "default": {}},
        "executor": {"type": dict, "required": False, "default": {}},
        "observer": {"type": dict, "required": False, "default": {}},
        "learning": {"type": dict, "required": False, "default": {}},
        "doctor": {"type": dict, "required": False, "default": {}},
    },
}

# Environment variable override prefixes
_ENV_PREFIX = "SHUNYA_"
_ENV_SECTION_SEP = "__"
_ENV_KEY_SEP = "_"


class ConfigValidationError(Exception):
    """Raised when configuration fails validation."""


class Config:
    """Application configuration.

    Loads from YAML files with environment variable overrides.
    Per-environment config files are supported via ``environment`` setting.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._source_files: List[str] = []

    @property
    def source_files(self) -> List[str]:
        """Paths of config files that were loaded."""
        return list(self._source_files)

    def load(self, path: Optional[str] = None, environment: Optional[str] = None) -> "Config":
        """Load configuration from YAML file(s).

        Args:
            path: Path to YAML config file. If None, looks for ``config.yaml``
                  in the current directory, then ``~/.shunya/config.yaml``.
            environment: Environment name for per-env overrides (e.g. "production").
                         If set, loads ``{path}.{environment}.yaml`` after the base file.

        Returns:
            Self for chaining.
        """
        resolved_path = self._find_config(path)
        if resolved_path:
            with open(resolved_path) as f:
                data = yaml.safe_load(f) or {}
            self._data = data
            self._source_files.append(str(resolved_path))

        # Load per-environment overrides
        env = environment or self._data.get("app", {}).get("environment", "development")
        if resolved_path:
            env_path = resolved_path.with_suffix(f".{env}.yaml")
            if env_path.exists():
                with open(env_path) as f:
                    env_data = yaml.safe_load(f) or {}
                self._deep_merge(self._data, env_data)
                self._source_files.append(str(env_path))

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Validate and apply defaults
        self._validate_and_apply_defaults()

        return self

    def load_dict(self, data: Dict[str, Any]) -> "Config":
        """Load configuration from a dictionary. Useful for testing."""
        self._data = data
        self._apply_env_overrides()
        self._validate_and_apply_defaults()
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dot-separated key (e.g. 'logging.level')."""
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire config section as a dict."""
        return self._data.get(section, {})

    def to_dict(self) -> Dict[str, Any]:
        """Return full config as a dictionary."""
        return dict(self._data)

    def _find_config(self, path: Optional[str] = None) -> Optional[Path]:
        if path:
            p = Path(path)
            if p.exists():
                return p
            return None
        # Default search paths
        candidates = [Path("config.yaml"), Path.home() / ".shunya" / "config.yaml"]
        for c in candidates:
            if c.exists():
                return c
        return None

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        Convention:
          SHUNYA_{SECTION}__{KEY}={value}
        Example:
          SHUNYA_LOGGING__LEVEL=DEBUG
          SHUNYA_PERSISTENCE__DATABASE_URL=postgresql://...
        """
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(_ENV_PREFIX):
                continue
            remainder = env_key[len(_ENV_PREFIX):]
            if _ENV_SECTION_SEP not in remainder:
                continue
            section, key = remainder.split(_ENV_SECTION_SEP, 1)
            section = section.lower()
            key = key.lower()
            if section not in self._data:
                self._data[section] = {}
            self._data[section][key] = self._coerce_value(
                section, key, env_value
            )

    def _coerce_value(self, section: str, key: str, value: str) -> Any:
        """Coerce environment variable string to the expected type."""
        section_schema = CONFIG_SCHEMA.get(section, {})
        field_schema = section_schema.get(key, {})
        expected_type = field_schema.get("type")
        if expected_type == bool:
            return value.lower() in ("1", "true", "yes", "on")
        if expected_type == int:
            return int(value)
        if expected_type == float:
            return float(value)
        if expected_type == list:
            return [v.strip() for v in value.split(",")]
        return value  # string or unknown

    def _validate_and_apply_defaults(self) -> None:
        errors: List[str] = []
        for section_name, section_schema in CONFIG_SCHEMA.items():
            if section_name not in self._data:
                self._data[section_name] = {}
            section_data = self._data[section_name]
            for field_name, field_schema in section_schema.items():
                if field_name not in section_data:
                    if field_schema.get("required"):
                        if field_schema.get("default") is not None:
                            section_data[field_name] = field_schema["default"]
                        else:
                            errors.append(
                                f"Missing required config field: {section_name}.{field_name}"
                            )
                    else:
                        if field_schema.get("default") is not None:
                            section_data[field_name] = field_schema["default"]
                else:
                    # Type check
                    expected_type = field_schema.get("type")
                    if expected_type and expected_type is not type(None):
                        actual = section_data[field_name]
                        if not isinstance(actual, expected_type):
                            # Allow int->float promotion
                            if expected_type == float and isinstance(actual, int):
                                section_data[field_name] = float(actual)
                            else:
                                errors.append(
                                    f"Config field {section_name}.{field_name}: "
                                    f"expected {expected_type.__name__}, "
                                    f"got {type(actual).__name__}"
                                )
        if errors:
            raise ConfigValidationError("\n".join(errors))


# ---- Module-level convenience -----------------------------------------------

_config: Optional[Config] = None


def get_config() -> Config:
    """Return the application-wide Config instance (lazily loaded)."""
    global _config
    if _config is None:
        _config = Config()
        _config.load()
    return _config


def reset_config() -> None:
    """Reset the global config. Useful for testing."""
    global _config
    _config = None