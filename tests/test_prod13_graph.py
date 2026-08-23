"""PROD-13: Full object graph awareness validation.

Chain: A evolves to v2 → B depends_on A → C depends_on B.
Expected cycles:
  A  → version 2
  B  → resolved_relations: [A]  (then B propagates to v2)
  C  → resolved_relations: [B]  (then C propagates to v2)
"""
import json
import sys
sys.path.insert(0, '.')


def _create(client, state):
    r = client.post('/api/v1/objects/', json={'type': 'entity', 'state': state})
    assert r.status_code in (200, 201), f"Create failed: {r.get_json()}"
    return r.get_json().get('object_id') or r.get_json().get('id')


def _print(label, obj):
    print(f"{label}: {json.dumps(obj.state, indent=2)}")


def _cycle(obj, label, de, ea):
    """Run one decision → execute cycle and return the action."""
    action = de(obj)
    print(f"  {label}: {json.dumps(action, indent=2)}")
    if action['type'] == 'update':
        ea(obj, action)
    return action


def test_a_to_b_to_c_chain(app, client):
    """Full A→B→C relation chain validation."""
    from app.objects.models import Object
    from app.runtime.decision_engine import get_next_action
    from app.execution_engine.engine import execute_action
    from app import db

    with app.app_context():
        a_id = _create(client, {})
        print(f"\n=== A (id={a_id}) ===")
        a = Object.query.get(a_id)
        _print("A start", a)

        # Evolve A to version 2
        _cycle(a, "A cycle 1", get_next_action, execute_action)
        _print("A after cycle 1", a)
        _cycle(a, "A cycle 2", get_next_action, execute_action)
        _print("A after cycle 2", a)
        assert a.state.get('version') == 2, f"A should be v2, got {a.state}"

        print("\n=== B (depends_on A) ===")
        b_id = _create(client, {'relations': [{'type': 'depends_on', 'target_id': a_id}]})
        b = Object.query.get(b_id)
        _print("B start", b)

        # B resolves A
        _cycle(b, "B cycle 1", get_next_action, execute_action)
        _print("B after cycle 1", b)
        assert b.state.get('resolved_relations') == [a_id], \
            f"B should have resolved [{a_id}], got {b.state.get('resolved_relations')}"
        print("  ✅ B resolved A")

        # B propagates to version 2 (so downstream C can depend on B)
        _cycle(b, "B cycle 2", get_next_action, execute_action)
        _print("B after cycle 2", b)
        _cycle(b, "B cycle 3", get_next_action, execute_action)
        _print("B after cycle 3", b)
        assert b.state.get('version') == 2, f"B should be v2, got {b.state}"
        print("  ✅ B reached version 2 (graph propagation)")

        print("\n=== C (depends_on B) ===")
        c_id = _create(client, {'relations': [{'type': 'depends_on', 'target_id': b_id}]})
        c = Object.query.get(c_id)
        _print("C start", c)

        # C resolves B
        _cycle(c, "C cycle 1", get_next_action, execute_action)
        _print("C after cycle 1", c)
        assert c.state.get('resolved_relations') == [b_id], \
            f"C should have resolved [{b_id}], got {c.state.get('resolved_relations')}"
        print("  ✅ C resolved B")

        # C propagates to version 2
        _cycle(c, "C cycle 2", get_next_action, execute_action)
        _print("C after cycle 2", c)
        _cycle(c, "C cycle 3", get_next_action, execute_action)
        _print("C after cycle 3", c)
        assert c.state.get('version') == 2, f"C should be v2, got {c.state}"
        print("  ✅ C reached version 2 (graph propagation)")

        # Final noop check
        final = get_next_action(c)
        assert final['type'] == 'noop', f"C should noop, got {final}"

        print(f"\n{'='*50}")
        print("FINAL STATES")
        print(f"{'='*50}")
        _print("A", a)
        _print("B", b)
        _print("C", c)
        print(f"\n✅ PROD-13 VALIDATION PASSED")
        print(f"  • A → version 2")
        print(f"  • B → depends_on A → resolved [{a_id}] → version 2")
        print(f"  • C → depends_on B → resolved [{b_id}] → version 2")
        print(f"  • All relations structural — no business logic")
        print(f"  • Graph propagates: A@v2 → B@v2 → C@v2\n")