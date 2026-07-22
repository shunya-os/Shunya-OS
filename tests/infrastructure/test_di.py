"""Tests for INFR-001: Dependency Injection Container."""

import pytest
from app.shunya.di import DIContainer, get_container, reset_container


class _IService:
    def greet(self) -> str:
        ...


class _ServiceA(_IService):
    def greet(self) -> str:
        return "Hello from A"


class _ServiceB(_IService):
    def __init__(self, service_a: _IService) -> None:
        self.service_a = service_a

    def greet(self) -> str:
        return f"Hello from B, got {self.service_a.greet()}"


class _ServiceWithDefault:
    def __init__(self, service_a: _IService, timeout: int = 30) -> None:
        self.service_a = service_a
        self.timeout = timeout


class TestDIContainer:
    def setup_method(self) -> None:
        self.container = DIContainer()

    def test_register_singleton_resolves_same_instance(self) -> None:
        self.container.register_singleton(_IService, _ServiceA)
        instance1 = self.container.resolve(_IService)
        instance2 = self.container.resolve(_IService)
        assert instance1 is instance2

    def test_register_singleton_with_instance(self) -> None:
        instance = _ServiceA()
        self.container.register_singleton(_IService, instance=instance)
        resolved = self.container.resolve(_IService)
        assert resolved is instance

    def test_register_factory_resolves_new_instance_each_time(self) -> None:
        self.container.register_factory(_IService, lambda: _ServiceA())
        instance1 = self.container.resolve(_IService)
        instance2 = self.container.resolve(_IService)
        assert instance1 is not instance2

    def test_auto_wiring(self) -> None:
        self.container.register_singleton(_IService, _ServiceA)
        self.container.register_singleton(_ServiceB)
        resolved = self.container.resolve(_ServiceB)
        assert isinstance(resolved, _ServiceB)
        assert resolved.greet() == "Hello from B, got Hello from A"

    def test_resolve_not_registered_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="No registration found"):
            self.container.resolve(_IService)

    def test_is_registered(self) -> None:
        assert not self.container.is_registered(_IService)
        self.container.register_singleton(_IService, _ServiceA)
        assert self.container.is_registered(_IService)

    def test_clear_removes_all_registrations(self) -> None:
        self.container.register_singleton(_IService, _ServiceA)
        self.container.clear()
        assert not self.container.is_registered(_IService)

    def test_auto_wire_with_default_parameter(self) -> None:
        self.container.register_singleton(_IService, _ServiceA)
        self.container.register_singleton(_ServiceWithDefault)
        resolved = self.container.resolve(_ServiceWithDefault)
        assert resolved.timeout == 30

    def test_module_level_get_container(self) -> None:
        reset_container()
        c1 = get_container()
        c2 = get_container()
        assert c1 is c2

    def test_reset_container_creates_new_instance(self) -> None:
        c1 = get_container()
        reset_container()
        c2 = get_container()
        assert c1 is not c2