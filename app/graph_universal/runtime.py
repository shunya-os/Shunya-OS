"""
SHUNYA Universal Business Graph — Bootstrap and Middleware
"""

from flask import request, jsonify
from datetime import datetime, timezone

from app.graph_universal.entity import Entity, get_store as get_entity_store
from app.graph_universal.relationship import Relationship, get_store as get_rel_store
from app.graph_universal.identity import get_resolver
from app.graph_universal.property import get_store as get_prop_store
from app.graph_universal.event import get_store as get_event_store
from app.graph_universal.traversal import get_engine


def register_graph_middleware(app) -> None:
    @app.before_request
    def _check_graph_inspect():
        if request.args.get("inspect_graph"):
            return jsonify(_inspect_graph())
        return None


def _inspect_graph() -> dict:
    return {
        "entities": {"total": get_entity_store().count},
        "relationships": {"total": get_rel_store().count},
        "identities": {"total": get_resolver().count},
        "properties": {"total": get_prop_store().count},
        "events": {"total": get_event_store().count},
        "inspection_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_graph_data() -> None:
    es = get_entity_store()
    rs = get_rel_store()
    ir = get_resolver()
    ps = get_prop_store()
    gs = get_event_store()

    # Create entities
    entities = [
        Entity(entity_id="ent_jupiter", name="Jupiter Media", entity_type="organization", aliases=["Jupiter Media Corp", "JMC"]),
        Entity(entity_id="ent_nexus", name="Nexus Ventures", entity_type="organization", aliases=["Nexus", "NVI"]),
        Entity(entity_id="ent_sarah", name="Sarah Chen", entity_type="person", aliases=["Sarah C.", "SC"]),
        Entity(entity_id="ent_marcus", name="Marcus Webb", entity_type="person", aliases=["Marcus W.", "MW"]),
        Entity(entity_id="ent_agreement", name="Jupiter Media Partnership", entity_type="agreement"),
        Entity(entity_id="ent_northgate", name="Northgate Manufacturing", entity_type="portfolio_company"),
    ]
    for e in entities:
        es.add(e)
        ir.register(e)

    # Create relationships
    rs.add(Relationship(rel_id="rel_sarah_agreement", source_id="ent_sarah", target_id="ent_agreement", rel_type="manages", confidence=0.95))
    rs.add(Relationship(rel_id="rel_marcus_northgate", source_id="ent_marcus", target_id="ent_northgate", rel_type="manages", confidence=0.9))
    rs.add(Relationship(rel_id="rel_nexus_agreement", source_id="ent_nexus", target_id="ent_agreement", rel_type="owns", confidence=1.0))
    rs.add(Relationship(rel_id="rel_agreement_jupiter", source_id="ent_agreement", target_id="ent_jupiter", rel_type="partners_with", confidence=0.95))

    # Set properties
    ps.set_property("ent_agreement", "revenue_share", "60/40", source="contract", confidence=1.0)
    ps.set_property("ent_agreement", "duration_months", 18, source="contract", confidence=1.0)
    ps.set_property("ent_northgate", "employees", 340, source="filing", confidence=0.9)

    # Record events
    gs.record("entity_created", "ent_jupiter", {"name": "Jupiter Media"})
    gs.record("entity_created", "ent_agreement", {"name": "Jupiter Media Partnership"})
    gs.record("relationship_added", "ent_sarah", {"rel_type": "manages", "target": "ent_agreement"})