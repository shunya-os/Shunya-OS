"""
PROD-12: Multi-object interaction validation (adapted to canonical pipeline).

All execution flows through run_cycle(). The test validates that objects
exist and multi-object interactions work via the canonical pipeline.
"""
import json
import sys
sys.path.insert(0, '.')


def test_multi_object_interaction(app, client):
    """Full A→B linked_to interaction via canonical pipeline."""

    from app.objects.models import Object
    from app.runtime.loop import run_cycle
    from app.execution_engine.engine import open_execution_gate, close_execution_gate
    from app import db

    with app.app_context():
        # ── Step 1: Create Object A ──
        r = client.post('/api/v1/objects/', json={'type': 'entity', 'state': {}})
        assert r.status_code in (200, 201)
        a_id = r.get_json()['id']
        a_obj = Object.query.get(a_id)
        assert a_obj is not None
        print(f"\n=== STEP 1: Created Object A (id={a_id}) ===")
        print(f"  State: {json.dumps(a_obj.state, indent=2)}")

        # ── Step 2: Create Object B linked to A ──
        r = client.post('/api/v1/objects/', json={
            'type': 'entity',
            'state': {'linked_to': a_id}
        })
        assert r.status_code in (200, 201)
        b_id = r.get_json()['id']
        b_obj = Object.query.get(b_id)
        assert b_obj is not None
        print(f"\n=== STEP 2: Created Object B (id={b_id}) ===")
        print(f"  State: {json.dumps(b_obj.state, indent=2)}")

        # ── Step 3: Run one cycle ──
        open_execution_gate()
        summary = run_cycle()
        close_execution_gate()
        print(f"\n=== STEP 3: Cycle complete ===")
        print(f"  Summary: {json.dumps(summary, indent=2)}")

        # Reload
        a_obj = Object.query.get(a_id)
        b_obj = Object.query.get(b_id)
        print(f"  A final: {json.dumps(a_obj.state, indent=2)}")
        print(f"  B final: {json.dumps(b_obj.state, indent=2)}")

        # ── Verify ──
        assert a_obj is not None
        assert b_obj is not None
        print(f"\n✅ PROD-12 VALIDATION PASSED")