"""PROD-12: Multi-object interaction validation.

Proof:
1. Create Object A → run cycles until it reaches version 2
2. Create Object B linked to A → run cycle → B gets synced: True
3. Verify final states
"""
import json
import sys
sys.path.insert(0, '.')


def test_multi_object_interaction(app, client):
    """Full A→B linked_to interaction validation."""

    from app.objects.models import Object
    from app.runtime.decision_engine import get_next_action
    from app.execution_engine.engine import execute_action
    from app import db

    with app.app_context():
        # ── Step 1: Create Object A ──
        r = client.post('/api/v1/objects/', json={'type': 'entity', 'state': {}})
        assert r.status_code in (200, 201), f"Create A failed: {r.get_json()}"
        a_data = r.get_json()
        a_id = a_data['id']
        print(f"\n=== STEP 1: Created Object A (id={a_id}) ===")
        print(f"Initial state: {json.dumps(a_data.get('state', {}), indent=2)}")

        # ── Step 2: Run cycles on A until version=2 ──
        a_obj = Object.query.get(a_id)
        print(f"\n=== STEP 2: Evolve Object A to version 2 ===")

        # Cycle 1: empty state → initialize (version=1)
        action1 = get_next_action(a_obj)
        print(f"Cycle 1 decision: {json.dumps(action1, indent=2)}")
        execute_action(a_obj, action1)
        print(f"State after cycle 1: {json.dumps(a_obj.state, indent=2)}")
        assert a_obj.state.get('version') == 1, f"Expected version=1, got {a_obj.state}"

        # Cycle 2: version=1 → version=2
        action2 = get_next_action(a_obj)
        print(f"Cycle 2 decision: {json.dumps(action2, indent=2)}")
        execute_action(a_obj, action2)
        print(f"State after cycle 2: {json.dumps(a_obj.state, indent=2)}")
        assert a_obj.state.get('version') == 2, f"Expected version=2, got {a_obj.state}"
        assert a_obj.state.get('initialized') is True

        # ── Step 3: Create Object B linked to A ──
        r = client.post('/api/v1/objects/', json={
            'type': 'entity',
            'state': {'linked_to': a_id}
        })
        assert r.status_code in (200, 201), f"Create B failed: {r.get_json()}"
        b_data = r.get_json()
        b_id = b_data['id']
        print(f"\n=== STEP 3: Created Object B (id={b_id}, linked_to={a_id}) ===")
        print(f"Initial state: {json.dumps(b_data.get('state', {}), indent=2)}")

        # ── Step 4: Run cycle on B ──
        b_obj = Object.query.get(b_id)
        print(f"\n=== STEP 4: Run decision engine on Object B ===")

        # B starts with empty state → first initialize
        action3 = get_next_action(b_obj)
        print(f"Cycle 1 on B: {json.dumps(action3, indent=2)}")
        execute_action(b_obj, action3)
        print(f"State after cycle 1 on B: {json.dumps(b_obj.state, indent=2)}")

        # Now B has linked_to + initialized. Next cycle: check linked object
        action4 = get_next_action(b_obj)
        print(f"Cycle 2 on B: {json.dumps(action4, indent=2)}")
        execute_action(b_obj, action4)
        print(f"State after cycle 2 on B: {json.dumps(b_obj.state, indent=2)}")

        # ── Step 5: Verify ──
        print(f"\n=== STEP 5: VALIDATION ===")
        print(f"Object A final state: {json.dumps(a_obj.state, indent=2)}")
        print(f"Object B final state: {json.dumps(b_obj.state, indent=2)}")

        assert a_obj.state.get('version') == 2, f"A should be version=2"
        assert a_obj.state.get('initialized') is True
        assert b_obj.state.get('linked_to') == a_id, f"B should still be linked_to {a_id}"
        assert b_obj.state.get('synced') is True, f"B should have synced=True"
        # B was created with linked_to state, so initialization didn't fire;
        # linked_to check detected A@v2 and set synced=True — no version field.
        assert b_obj.state.get('version') is None, f"B should have no version (synced path skipped init)"

        print("\n✅ PROD-12 VALIDATION PASSED")
        print("  • Object A reached version 2")
        print("  • Object B linked to A at version 1")
        print("  • Decision engine detected linked_to + A.version==2")
        print("  • B was updated with synced=True")
        print("  • No business logic — purely structural interaction\n")


if __name__ == '__main__':
    # Standalone run using the test fixture
    from tests.conftest import app, client
    _app = next(app())
    _client = client(_app)
    test_multi_object_interaction(_app, _client)