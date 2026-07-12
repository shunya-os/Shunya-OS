"""Formal ontology engine — wraps the 8 vertical templates with contracts.
Port of the half-done TypeScript architecture (OntologyRegistry, OntologyValidator,
OntologyDiagnostics, OntologyLoader) tailored for Shunya-OS verticals.

Dataclasses + registries provide a typed, introspectable ontology layer
on top of the dict-based VERTICAL_TEMPLATES. This is the source of truth
for all entity-type definitions across verticals.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ── Status Enum ──

class OntologyStatus:
    ACTIVE = "active"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


# ── Core Data Classes ──

@dataclass
class OntologyEntity:
    """A single entity type in the ontology."""
    type: str
    label: str
    label_plural: str
    icon: str
    primary_field: str
    schema: List[Dict[str, Any]]
    statuses: List[str]
    layout: str = "table"
    searchable_fields: List[str] = field(default_factory=list)
    code_prefix: Optional[str] = None


@dataclass
class VerticalOntology:
    """A vertical's full ontology definition."""
    id: str
    name: str
    icon: str
    description: str
    theme_icon: str
    default_brand_color: str
    default_brand_secondary: str
    code_prefix: str
    entities: Dict[str, OntologyEntity]
    dashboard_metrics: List[Dict[str, str]] = field(default_factory=list)
    quick_actions: List[Dict[str, str]] = field(default_factory=list)
    status: str = OntologyStatus.ACTIVE


# ── Registry ──

class OntologyRegistry:
    """Registry of all vertical ontologies.
    
    Port of the half-done TypeScript OntologyRegistry — adapted from
    flat collections (organizations/actors/workflows) to vertical-centred
    registry that maps vertical-id → VerticalOntology.
    """

    def __init__(self):
        self._verticals: Dict[str, VerticalOntology] = {}

    def register(self, vertical: VerticalOntology) -> None:
        """Register a vertical ontology."""
        self._verticals[vertical.id] = vertical

    def get(self, id: str) -> Optional[VerticalOntology]:
        """Get a vertical ontology by id."""
        return self._verticals.get(id)

    def list(self) -> List[VerticalOntology]:
        """List all registered vertical ontologies."""
        return list(self._verticals.values())

    def count(self) -> int:
        """Count registered vertical ontologies."""
        return len(self._verticals)

    def find_entity_type(self, entity_type: str) -> Optional[OntologyEntity]:
        """Find which vertical defines this entity type."""
        for v in self._verticals.values():
            if entity_type in v.entities:
                return v.entities[entity_type]
        return None

    def find_vertical_by_entity(self, entity_type: str) -> Optional[VerticalOntology]:
        """Find the vertical that contains a given entity type."""
        for v in self._verticals.values():
            if entity_type in v.entities:
                return v
        return None

    def all_entity_types(self) -> Dict[str, str]:
        """Return a flat map of entity_type → vertical_id."""
        result: Dict[str, str] = {}
        for v in self._verticals.values():
            for et in v.entities:
                result[et] = v.id
        return result

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serialize all verticals to JSON-compatible dicts."""
        return [_vertical_to_dict(v) for v in self._verticals.values()]


def _vertical_to_dict(v: VerticalOntology) -> Dict[str, Any]:
    return {
        "id": v.id,
        "name": v.name,
        "icon": v.icon,
        "description": v.description,
        "theme_icon": v.theme_icon,
        "default_brand_color": v.default_brand_color,
        "default_brand_secondary": v.default_brand_secondary,
        "code_prefix": v.code_prefix,
        "status": v.status,
        "entity_count": len(v.entities),
        "entities": {
            et: {
                "type": e.type,
                "label": e.label,
                "label_plural": e.label_plural,
                "icon": e.icon,
                "primary_field": e.primary_field,
                "layout": e.layout,
                "statuses": e.statuses,
                "schema_fields": [f["name"] for f in e.schema],
                "code_prefix": e.code_prefix,
            }
            for et, e in v.entities.items()
        },
        "dashboard_metrics": v.dashboard_metrics,
        "quick_actions": v.quick_actions,
    }


# ── Validator ──

class OntologyValidator:
    """Validates ontology structure and cross-vertical references.
    
    Port of the half-done TypeScript OntologyValidator — adapted from
    intent cross-references to entity-type cross-references.
    """

    def __init__(self, registry: Optional[OntologyRegistry] = None):
        self._registry = registry

    def set_registry(self, registry: OntologyRegistry) -> None:
        """Wire up the registry for cross-vertical reference checking."""
        self._registry = registry

    def validate_vertical(self, vertical: VerticalOntology) -> List[str]:
        """Validate a single vertical ontology. Returns list of issues (empty = valid)."""
        issues: List[str] = []

        # Each entity must have a schema with at least one field
        for et, ent in vertical.entities.items():
            if not ent.schema:
                issues.append(f"{vertical.id}/{et}: empty schema — at least one field required")
            if not ent.statuses:
                issues.append(f"{vertical.id}/{et}: no statuses defined — at least one required")
            if not ent.primary_field:
                issues.append(f"{vertical.id}/{et}: no primary_field defined")

            # Check each schema field
            for field in ent.schema:
                name = field.get("name", "?")
                ftype = field.get("type", "?")
                if not name or name == "?":
                    issues.append(f"{vertical.id}/{et}: schema field missing 'name'")

                # Check for referenced entity types that don't exist in any vertical
                ref = field.get("entity_type")
                if ref and ref != et:
                    if self._registry and not self._registry.find_entity_type(ref):
                        issues.append(
                            f"{vertical.id}/{et}.{name}: references unknown entity type '{ref}'"
                        )

        return issues

    def validate_all(self, registry: OntologyRegistry) -> Dict[str, List[str]]:
        """Validate all verticals in a registry. Returns {vertical_id: [issues]}."""
        results: Dict[str, List[str]] = {}
        for v in registry.list():
            results[v.id] = self.validate_vertical(v)
        return results


# ── Diagnostics ──

@dataclass
class OntologyDiagnosticsReport:
    """Health report for the ontology registry.
    
    Port of the half-done TypeScript OntologyDiagnosticsReport.
    """
    verticals: int
    entity_types: int
    total_schema_fields: int
    status_counts: Dict[str, int]
    entity_types_by_vertical: Dict[str, int]
    unused_entity_types: Optional[List[str]] = None
    warnings: List[str] = field(default_factory=list)


class OntologyDiagnostics:
    """Generates health reports for the ontology registry.
    
    Port of the half-done TypeScript OntologyDiagnostics — instead of
    counting organizations/actors/workflows, it counts verticals,
    entity types, and schema fields.
    """

    def analyze(self, registry: OntologyRegistry) -> OntologyDiagnosticsReport:
        """Run diagnostics and return a health report."""
        entity_types = 0
        total_fields = 0
        status_counts: Dict[str, int] = {}
        by_vertical: Dict[str, int] = {}
        warnings: List[str] = []

        for v in registry.list():
            et_count = len(v.entities)
            entity_types += et_count
            by_vertical[v.id] = et_count

            s = v.status or OntologyStatus.ACTIVE
            status_counts[s] = status_counts.get(s, 0) + 1

            for ent in v.entities.values():
                total_fields += len(ent.schema)
                if not ent.searchable_fields:
                    warnings.append(
                        f"{v.id}/{ent.type}: no searchable_fields set — may affect search UX"
                    )

        # Detect cross-vertical overlap in entity type names
        type_map: Dict[str, List[str]] = {}
        for v in registry.list():
            for et in v.entities:
                type_map.setdefault(et, []).append(v.id)
        for et, verts in type_map.items():
            if len(verts) > 1:
                warnings.append(
                    f"Entity type '{et}' is defined in multiple verticals: {', '.join(verts)}"
                )

        return OntologyDiagnosticsReport(
            verticals=registry.count(),
            entity_types=entity_types,
            total_schema_fields=total_fields,
            status_counts=status_counts,
            entity_types_by_vertical=by_vertical,
            warnings=warnings,
        )


# ── Loader ──

class OntologyLoader:
    """Loads the ontology registry from the vertical templates dict.
    
    Port of the half-done TypeScript OntologyLoader — instead of returning
    an empty OntologyRegistry, it hydrates from VERTICAL_TEMPLATES.
    """

    def load(self) -> OntologyRegistry:
        """Load VERTICAL_TEMPLATES into a populated OntologyRegistry."""
        from app.shunya.verticals import VERTICAL_TEMPLATES

        registry = OntologyRegistry()

        for vid, vdata in VERTICAL_TEMPLATES.items():
            entities: Dict[str, OntologyEntity] = {}

            for et_def in vdata.get("entity_types", []):
                entity = OntologyEntity(
                    type=et_def["type"],
                    label=et_def.get("label", et_def["type"].title()),
                    label_plural=et_def.get("label_plural", et_def.get("label", et_def["type"].title())),
                    icon=et_def.get("icon", "📄"),
                    primary_field=et_def.get("primary_field", "name"),
                    schema=et_def.get("schema", []),
                    statuses=et_def.get("statuses", ["active"]),
                    layout=et_def.get("layout", "table"),
                    searchable_fields=[
                        f["name"] for f in et_def.get("schema", [])
                        if f.get("type") in ("text", "textarea", "email", "phone")
                    ],
                    code_prefix=vdata.get("code_prefix"),
                )
                entities[entity.type] = entity

            vertical = VerticalOntology(
                id=vid,
                name=vdata.get("label", vid.title()),
                icon=vdata.get("icon", "📄"),
                description=vdata.get("description", ""),
                theme_icon=vdata.get("theme_icon", vdata.get("icon", "📄")),
                default_brand_color=vdata.get("default_brand_color", "#2563eb"),
                default_brand_secondary=vdata.get("default_brand_secondary", "#7c3aed"),
                code_prefix=vdata.get("code_prefix", "BIZ"),
                entities=entities,
                dashboard_metrics=vdata.get("dashboard_metrics", []),
                quick_actions=vdata.get("quick_actions", []),
                status=OntologyStatus.ACTIVE,
            )
            registry.register(vertical)

        return registry