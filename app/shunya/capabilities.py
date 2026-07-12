"""Formal capability catalog — mirrors the half-done TypeScript architecture."""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class CapabilityStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    DEPRECATED = "deprecated"


@dataclass
class Capability:
    id: str
    name: str
    status: CapabilityStatus = CapabilityStatus.PLANNED
    progress: int = 0
    depends_on: List[str] = field(default_factory=list)


@dataclass
class CapabilityCatalog:
    version: int = 1
    capabilities: List[Capability] = field(default_factory=list)


class CapabilityRegistry:
    """In-memory capability registry. Loaded from YAML catalog on startup."""

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._capabilities[capability.id] = capability

    def register_many(self, capabilities: List[Capability]) -> None:
        for c in capabilities:
            self.register(c)

    def get(self, id: str) -> Optional[Capability]:
        return self._capabilities.get(id)

    def list(self) -> List[Capability]:
        return list(self._capabilities.values())

    def count(self) -> int:
        return len(self._capabilities)

    def status_summary(self) -> dict:
        """Return counts per status."""
        result = {s.value: 0 for s in CapabilityStatus}
        for c in self._capabilities.values():
            result[c.status.value] = result.get(c.status.value, 0) + 1
        return result


class CapabilityLoader:
    """Loads a CapabilityCatalog from a YAML file and populates a registry."""

    @staticmethod
    def from_dict(data: dict) -> CapabilityCatalog:
        """Parse a catalog dict (from YAML) into typed objects."""
        caps = []
        for raw in data.get("capabilities", []):
            status_str = raw.get("status", "planned")
            try:
                status = CapabilityStatus(status_str)
            except ValueError:
                status = CapabilityStatus.PLANNED
            caps.append(Capability(
                id=raw["id"],
                name=raw["name"],
                status=status,
                progress=raw.get("progress", 0),
                depends_on=raw.get("dependsOn", raw.get("depends_on", [])),
            ))
        return CapabilityCatalog(
            version=data.get("version", 1),
            capabilities=caps,
        )

    @staticmethod
    def load_into_registry(
        data: dict,
        registry: Optional[CapabilityRegistry] = None,
    ) -> CapabilityRegistry:
        """Parse catalog YAML dict and register all capabilities."""
        if registry is None:
            registry = CapabilityRegistry()
        catalog = CapabilityLoader.from_dict(data)
        registry.register_many(catalog.capabilities)
        return registry

    @staticmethod
    def load_from_file(path: str) -> CapabilityCatalog:
        """Load and parse a YAML catalog file from disk."""
        import yaml
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return CapabilityLoader.from_dict(data)

    @staticmethod
    def load_file_into_registry(
        path: str,
        registry: Optional[CapabilityRegistry] = None,
    ) -> CapabilityRegistry:
        """Load YAML from file and register into (new or existing) registry."""
        if registry is None:
            registry = CapabilityRegistry()
        catalog = CapabilityLoader.load_from_file(path)
        registry.register_many(catalog.capabilities)
        return registry
