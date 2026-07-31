"""SHUNYA — Dependency Injection Container.

Provides a lightweight DI container with singleton and factory registration.
Constructor injection by type hint. Used by all engines for dependency wiring.

Architectural authority: INFR-001 (SHUNYA_IMPLEMENTATION_PROGRAM.md)
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")

_registry: Dict[str, Dict[str, Any]] = {}


class DIContainer:
    """Lightweight dependency injection container.

    Supports:
      - Singleton registration (same instance per request)
      - Factory registration (new instance per request)
      - Auto-wiring by constructor type hints
      - Lazy instantiation
    """

    def __init__(self) -> None:
        self._registrations: Dict[str, Dict[str, Any]] = {}

    def register_singleton(
        self, interface: Type[Any], implementation: Optional[Type[Any]] = None, instance: Optional[Any] = None
    ) -> None:
        """Register a singleton service.

        If `instance` is provided, that instance is returned on every resolve.
        Otherwise, `implementation` (or `interface` if implementation is None)
        is instantiated once on first resolve and cached.
        """
        key = _key_for(interface)
        self._registrations[key] = {
            "type": "singleton",
            "interface": interface,
            "implementation": implementation or interface,
            "instance": instance,
            "resolved": instance is not None,
        }

    def register_factory(
        self, interface: Type[Any], factory: Callable[[], Any]
    ) -> None:
        """Register a factory callable. A new instance is created on every resolve."""
        key = _key_for(interface)
        self._registrations[key] = {
            "type": "factory",
            "interface": interface,
            "factory": factory,
            "instance": None,
            "resolved": False,
        }

    def resolve(self, interface: Type[T]) -> T:
        """Resolve an instance of the given interface type.

        For singletons: returns the cached instance or creates and caches it.
        For factories: calls the factory and returns the result.
        Auto-wires constructor dependencies by resolving matching registrations.
        Raises `KeyError` if the interface is not registered.
        """
        key = _key_for(interface)
        reg = self._registrations.get(key)
        if reg is None:
            raise KeyError(
                f"No registration found for {interface.__name__}. "
                f"Register it with register_singleton() or register_factory() first."
            )

        if reg["type"] == "singleton":
            if reg["resolved"] and reg["instance"] is not None:
                return reg["instance"]
            instance = self._build(reg["implementation"])
            reg["instance"] = instance
            reg["resolved"] = True
            return instance

        if reg["type"] == "factory":
            return reg["factory"]()

        raise ValueError(f"Unknown registration type: {reg.get('type')}")

    def is_registered(self, interface: Type[Any]) -> bool:
        """Return True if the interface is registered."""
        return _key_for(interface) in self._registrations

    def clear(self) -> None:
        """Remove all registrations. Useful for test cleanup."""
        self._registrations.clear()

    def _build(self, cls: Type[T]) -> T:
        """Instantiate *cls* by resolving its constructor dependencies.

        Inspects ``__init__`` parameter annotations, resolves each parameter
        from the container, and calls ``cls(**resolved)``.
        """
        sig = inspect.signature(cls.__init__)
        params: Dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue  # skip *args and **kwargs
            if param.annotation is inspect.Parameter.empty:
                raise ValueError(
                    f"Cannot auto-wire parameter '{name}' of {cls.__name__}: "
                    f"missing type annotation"
                )
            try:
                params[name] = self.resolve(param.annotation)
            except KeyError:
                if param.default is not inspect.Parameter.empty:
                    params[name] = param.default
                else:
                    raise
        return cls(**params)

    def __repr__(self) -> str:
        regs = list(self._registrations.keys())
        return f"DIContainer(registrations={regs})"


# ---- Module-level convenience -----------------------------------------------

_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Return the application-wide DI container (lazily created)."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container() -> None:
    """Reset the global container. Useful for testing."""
    global _container
    _container = None


def _key_for(interface: Type[Any]) -> str:
    return f"{interface.__module__}.{interface.__qualname__}"