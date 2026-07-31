"""Tests for INFR-002: Configuration System."""

import os
import tempfile
import yaml
import pytest
from app.shunya.config import Config, ConfigValidationError, get_config, reset_config


class TestConfig:
    def test_load_defaults(self) -> None:
        cfg = Config().load_dict({})
        assert cfg.get("app.name") == "shunya"
        assert cfg.get("logging.level") == "INFO"
        assert cfg.get("persistence.database_url") == "sqlite:///:memory:"

    def test_override_from_dict(self) -> None:
        cfg = Config().load_dict({"logging": {"level": "DEBUG"}})
        assert cfg.get("logging.level") == "DEBUG"

    def test_get_section(self) -> None:
        cfg = Config().load_dict({"logging": {"level": "DEBUG", "format": "json"}})
        section = cfg.get_section("logging")
        assert section["level"] == "DEBUG"
        assert section["format"] == "json"

    def test_get_with_dot_separated_key(self) -> None:
        cfg = Config().load_dict({"app": {"name": "test-app"}})
        assert cfg.get("app.name") == "test-app"

    def test_get_default_when_not_present(self) -> None:
        cfg = Config().load_dict({})
        assert cfg.get("nonexistent.key", "fallback") == "fallback"

    def test_get_none_default_when_not_present(self) -> None:
        cfg = Config().load_dict({})
        assert cfg.get("nonexistent.key") is None

    def test_load_from_yaml_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"app": {"name": "yaml-test"}, "logging": {"level": "WARNING"}}, f)
            fname = f.name
        try:
            cfg = Config().load(fname)
            assert cfg.get("app.name") == "yaml-test"
            assert cfg.get("logging.level") == "WARNING"
        finally:
            os.unlink(fname)

    def test_missing_required_field_raises(self) -> None:
        cfg = Config()
        # Override schema to make a field required with no default
        from app.shunya.config import CONFIG_SCHEMA
        original = CONFIG_SCHEMA.get("persistence", {}).get("database_url", {})
        original_required = CONFIG_SCHEMA.get("persistence", {}).get("database_url", {}).get("required")
        try:
            # Temporarily make database_url required with no default
            from app.shunya.config import CONFIG_SCHEMA as schema
            schema["persistence"]["database_url"]["required"] = True
            schema["persistence"]["database_url"]["default"] = None
            with pytest.raises(ConfigValidationError, match="Missing required config"):
                cfg.load_dict({"persistence": {}})
        finally:
            schema["persistence"]["database_url"]["required"] = original_required if original_required is not None else False
            schema["persistence"]["database_url"]["default"] = original.get("default", "")

    def test_type_mismatch_raises(self) -> None:
        cfg = Config()
        with pytest.raises(ConfigValidationError, match="expected"):
            cfg.load_dict({"event_bus": {"max_queue_size": "not_an_int"}})

    def test_to_dict(self) -> None:
        cfg = Config().load_dict({"app": {"name": "test"}})
        d = cfg.to_dict()
        assert d["app"]["name"] == "test"

    def test_env_override(self) -> None:
        os.environ["SHUNYA_LOGGING__LEVEL"] = "ERROR"
        try:
            cfg = Config().load_dict({})
            assert cfg.get("logging.level") == "ERROR"
        finally:
            del os.environ["SHUNYA_LOGGING__LEVEL"]

    def test_env_override_bool(self) -> None:
        os.environ["SHUNYA_METRICS__ENABLED"] = "false"
        try:
            cfg = Config().load_dict({})
            assert cfg.get("metrics.enabled") is False
        finally:
            del os.environ["SHUNYA_METRICS__ENABLED"]

    def test_env_override_int(self) -> None:
        os.environ["SHUNYA_EVENT_BUS__MAX_QUEUE_SIZE"] = "5000"
        try:
            cfg = Config().load_dict({})
            assert cfg.get("event_bus.max_queue_size") == 5000
        finally:
            del os.environ["SHUNYA_EVENT_BUS__MAX_QUEUE_SIZE"]

    def test_module_level_get_config(self) -> None:
        reset_config()
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_reset_config_creates_new_instance(self) -> None:
        c1 = get_config()
        reset_config()
        c2 = get_config()
        assert c1 is not c2

    def test_source_files_tracking(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"app": {"name": "test"}}, f)
            fname = f.name
        try:
            cfg = Config().load(fname)
            assert fname in cfg.source_files[0]
        finally:
            os.unlink(fname)