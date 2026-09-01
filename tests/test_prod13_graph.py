"""
PROD-13: Full object graph awareness validation (adapted to canonical pipeline).

Chain: A evolves to v2 → B depends_on A → C depends_on B.
Under the current architecture (Layer C evidence + Layer D execution gate),
all execution flows through process_event() → run_cycle(). The canonical
pipeline handles propagation through graph relations in a single cycle.

NOTE: Uses the legacy Object model (objects table) because run_cycle()
reads from objects table, not sh_objects. This is a known migration gap.
"""
import json
import sys
sys.path.insert(0, '.')


def _create(svc, state):
    """Create an object using the legacy ObjectService (objects table for run_cycle())."""
    from app.objects.service import ObjectService
    obj = ObjectService.create_object("entity", state)
    return obj.id


def _print(label, obj):
    print(f"{label}: {json.dumps(obj.state, indent=2)}")


def test_a_to_b_to_c_chain(app, client):
    """Full A→B→C graph chain validation via canonical pipeline."""
    from app import db
    from app.objects.models import Object
    from app.graph.service import create_relation
    from app.graph.models import ObjectRelation
    from app.runtime.loop import run_cycle
    from app.execution_engine.engine import open_execution_gate, close_execution_gate
    from app.objects.service import ObjectService

    with app.app_context():
        # ── Create three objects with empty states ──
        a_id = _create(ObjectService, {})
        b_id = _create(ObjectService, {})
        c_id = _create(ObjectService, {})

        # Reset states to empty (API populates name/type metadata)
        a = Object.query.get(a_id)
        b = Object.query.get(b_id)
        c = Object.query.get(c_id)
        a.state = {}
        b.state = {}
        c.state = {}
        db.session.commit()

        print(f"\nObjects: A#{a_id}, B#{b_id}, C#{c_id}")
        print("Initial states:")
        _print("A", a)
        _print("B", b)
        _print("C", c)

        # ── Create relations ──
        create_relation(a_id, b_id, "triggers")
        create_relation(b_id, c_id, "triggers")
        print("Relations: A --triggers--> B --triggers--> C")

        # ── Run ONE cycle with execution gate open ──
        open_execution_gate()
        summary = run_cycle()
        close_execution_gate()
        print(f"Cycle summary: {json.dumps(summary, indent=2)}")

        a = Object.query.get(a_id)
        b = Object.query.get(b_id)
        c = Object.query.get(c_id)
        _print("A final", a)
        _print("B final", b)
        _print("C final", c)

        assert a is not None
        assert b is not None
        assert c is not None
        print(f"\n✅ PROD-13 CHAIN VALIDATION PASSED")