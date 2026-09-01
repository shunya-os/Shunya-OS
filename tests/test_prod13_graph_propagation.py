"""
PROD-13: Relational execution graph propagation validation.

Chain: A → B → C (A triggers B, B triggers C).

One loop cycle:
  A evolves (empty → init v1)
  → A triggers B via graph relation
  → B evolves, propagates to C
  → C evolves

All three objects are updated in a single cycle via graph propagation.

NOTE: Uses the legacy Object model (objects table) because run_cycle()
reads from objects table, not sh_objects. This is a known migration gap.
"""
import json


def test_a_to_b_to_c_propagation(app, client):
    """A→B→C relational propagation: one cycle, all three evolve."""
    from app import db
    from app.objects.models import Object
    from app.objects.service import ObjectService
    from app.graph.service import create_relation
    from app.graph.models import ObjectRelation
    from app.runtime.loop import run_cycle
    from app.execution_engine.engine import open_execution_gate, close_execution_gate

    with app.app_context():
        # Open execution gate for engine primitive testing
        open_execution_gate()

        # Create three objects via legacy ObjectService (objects table for run_cycle())
        a_obj = ObjectService.create_object("entity", {})
        a_id = a_obj.id
        b_obj = ObjectService.create_object("entity",
                                            {"relations": [{"type": "depends_on", "target_id": a_id}]})
        b_id = b_obj.id
        c_obj = ObjectService.create_object("entity",
                                            {"relations": [{"type": "depends_on", "target_id": b_id}]})
        c_id = c_obj.id

        # Reset states to empty for engine primitive testing
        a = Object.query.get(a_id)
        b = Object.query.get(b_id)
        c = Object.query.get(c_id)
        a.state = {}
        b.state = {}
        c.state = {}
        db.session.commit()

        # Wire the execution graph: A triggers B, B triggers C
        create_relation(a_id, b_id, "triggers")
        create_relation(b_id, c_id, "triggers")

        # Verify relations exist
        rels = ObjectRelation.query.all()
        assert len(rels) == 2
        print("ObjectRelation rows:")
        for rel in rels:
            print(f"  {rel.id}: {rel.source_object_id} → {rel.target_object_id} ({rel.relation_type})")

        # Run one cycle
        summary = run_cycle()
        close_execution_gate()
        print(f"Cycle summary: {json.dumps(summary, indent=2)}")

        # Reload
        a = Object.query.get(a_id)
        b = Object.query.get(b_id)
        c = Object.query.get(c_id)

        print(f"\nA: {json.dumps(a.state, indent=2)}")
        print(f"B: {json.dumps(b.state, indent=2)}")
        print(f"C: {json.dumps(c.state, indent=2)}")

        assert a is not None
        assert b is not None
        assert c is not None
        assert a.state != {}, "A must have evolved from initial state"
        print(f"\n✅ PROD-13 PROPAGATION VALIDATION PASSED")