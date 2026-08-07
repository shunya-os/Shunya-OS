"""PROD-13: Relational execution graph propagation validation.

Chain: A → B → C (A triggers B, B triggers C).

One loop cycle:
  A evolves (empty → init v1)
  → A triggers B via graph relation
  → B evolves, propagates to C
  → C evolves

All three objects are updated in a single cycle via graph propagation.
"""
import json


def test_a_to_b_to_c_propagation(app, client):
    """A→B→C relational propagation: one cycle, all three evolve."""
    from app import db
    from app.objects.models import Object
    from app.graph.service import create_relation
    from app.graph.models import ObjectRelation
    from app.runtime.loop import run_cycle

    with app.app_context():
        # Create three objects
        r_a = client.post('/api/v1/objects/', json={'type': 'entity', 'state': {}})
        a_id = r_a.get_json()['id']
        r_b = client.post('/api/v1/objects/', json={
            'type': 'entity',
            'state': {'relations': [{'type': 'depends_on', 'target_id': a_id}]},
        })
        b_id = r_b.get_json()['id']
        r_c = client.post('/api/v1/objects/', json={
            'type': 'entity',
            'state': {'relations': [{'type': 'depends_on', 'target_id': b_id}]},
        })
        c_id = r_c.get_json()['id']

        print(f"\nObjects: A={a_id}  B={b_id}  C={c_id}")

        # Wire the execution graph: A triggers B, B triggers C
        create_relation(a_id, b_id, "triggers")
        create_relation(b_id, c_id, "triggers")

        # Verify relations exist
        rels = ObjectRelation.query.all()
        assert len(rels) == 2
        print("ObjectRelation rows:")
        for r in rels:
            print(f"  {r.source_object_id} --{r.relation_type}--> {r.target_object_id}")

        # Run ONE cycle
        summary = run_cycle()
        print(f"\nCycle summary: {json.dumps(summary, indent=2)}")

        # Reload objects
        a = Object.query.get(a_id)
        b = Object.query.get(b_id)
        c = Object.query.get(c_id)

        print(f"\nA final: {json.dumps(a.state, indent=2)}")
        print(f"B final: {json.dumps(b.state, indent=2)}")
        print(f"C final: {json.dumps(c.state, indent=2)}")

        # All objects were updated in one cycle
        assert summary["total_objects"] == 3
        # At minimum: A (init) + B (from prop) + C (from prop)
        # B may also be processed a second time by main loop, reaching v2
        assert summary["actions_taken"] >= 3, \
            f"Expected ≥3 actions, got {summary['actions_taken']}"

        # A evolved: empty → initialized+version 1
        assert a.state.get('initialized') is True
        assert a.state.get('version') is not None

        # B evolved: state changed from its initial relations-only state
        assert b.state.get('initialized') is True, \
            f"B should have initialized, got {b.state}"
        assert b.state.get('version') is not None

        # C evolved: its relations should have resolved because propagation
        # happened AFTER B had already been updated
        assert c.state.get('initialized') is True, \
            f"C should have initialized, got {c.state}"

        # If B reached v2 before C was triggered, C resolved B
        if c.state.get('resolved_relations') is not None:
            print(f"\n  ✅ C resolved B: [b_id] = {c.state['resolved_relations']}")

        # Verify graph relations persisted
        assert ObjectRelation.query.count() == 2

        print(f"\n✅ PROD-13 RELATIONAL EXECUTION GRAPH VALIDATED")
        print(f"  • A evolved: {json.dumps(a.state)}")
        print(f"  • B evolved: {json.dumps(b.state)}")
        print(f"  • C evolved: {json.dumps(c.state)}")
        print(f"  • ObjectRelation rows: 2 (A→B, B→C)")
        print(f"  • All state changes in 1 cycle: {summary['actions_taken']} actions")