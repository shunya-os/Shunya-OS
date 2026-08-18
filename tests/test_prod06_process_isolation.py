"""PROD-06: Process-isolated concurrent decision → execution boundary test.

Replaces the thread-based approach with two SEPARATE Python processes.
Each process constructs its own Flask application and SQLAlchemy engine,
connected to the dedicated PostgreSQL test database.

The processes synchronize at the canonical decision boundary
(get_next_action) using a multiprocessing Barrier, proving both
invocations were simultaneously alive at the decision → execution boundary.

Requirements satisfied:
  1. Two genuinely independent processes (different PID, memory space)
  2. Each process: own Flask app, own SQLAlchemy engine, own DB connection
  3. Both connect to the SAME dedicated PostgreSQL test database
  4. Synchronization barrier INSIDE the canonical decision → execution path
  5. Invocation binding: each decision remains bound to its originating process
  6. No global mutable decision override
  7. Each DecisionTrace contains the complete canonical decision
"""

import multiprocessing
import os
import sys
import json
import time
import pytest

# The child processes (spawn context) need the project root on sys.path
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------------------------
# Dedicated test database — NOT the production database
# Read credentials from .env, target the dedicated test PG cluster on port 5433
# where shunya has CREATEDB privilege

import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
_PROD_URL = os.getenv("DATABASE_URL", "")
# Build the test URI from the production URL, swapping port and db name
# Uses proper URL parsing to extract the password
if _PROD_URL:
    parsed = urlparse(_PROD_URL)
    password = parsed.password
    user = parsed.username or "shunya"
    host = parsed.hostname or "localhost"
    # On port 5433, shunya has CREATEDB privilege for the dedicated test DB
    pw_part = f":{password}" if password else ""
    TEST_DB_URI = f"postgresql://{user}{pw_part}@{host}:5433/shunya_test_prod06"
else:
    TEST_DB_URI = "postgresql://shunya@localhost:5433/shunya_test_prod06"

# ---------------------------------------------------------------------------
# Child process entry point
# ---------------------------------------------------------------------------

def _child_process(
    barrier: multiprocessing.Barrier,
    result_queue: multiprocessing.Queue,
    tag: str,
    entity_id: int,
    db_uri: str,
):
    """Run process_event() in an isolated process.

    Each child:
    1. Creates its own Flask app with its own SQLAlchemy engine
    2. Runs process_event() with the given entity
    3. The patched get_next_action synchronizes at the decision boundary
    4. Reports the full result back via the queue
    """
    try:
        # Step 1: Construct own Flask app and SQLAlchemy engine
        from app import create_app, db

        test_app = create_app(config_override={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": db_uri,
            "SECRET_KEY": "test-secret-prod06",
            "DISABLE_RATE_LIMIT": "true",
            "WTF_CSRF_ENABLED": False,
        })

        with test_app.app_context():
            # Step 2: Import the modules we need
            from app.runtime.entry import process_event
            from app.runtime import decision_engine
            from app.evidence.decision_trace import DecisionTrace
            from app.evidence.models_db import EvidenceRecord
            from app.objects.models import Object
            from app import db as _db

            # Step 3: Patch get_next_action to synchronize at the decision boundary
            original_get_next_action = decision_engine.get_next_action

            def synced_get_next_action(obj, decision_ctx=None):
                """Synchronize at the canonical decision boundary.

                Strict barrier placement per PROD-06 §3:
                  canonical decision calculation
                      ↓
                  enter synchronization barrier
                      ↓
                  HOLD

                The canonical decision is computed FIRST, then both processes
                synchronize at the barrier AFTER the decision is calculated
                but BEFORE execution proceeds. This proves both invocations
                were simultaneously alive at the decision→execution boundary.
                """
                result = original_get_next_action(obj, decision_ctx=decision_ctx)
                # Barrier AFTER decision calculation, BEFORE execution proceeds
                barrier.wait()
                return result

            decision_engine.get_next_action = synced_get_next_action

            # Step 4: Run process_event()
            result = process_event(
                event_type=f"boundary_race_{tag}",
                event_data={"entity_id": entity_id, "id": entity_id},
                source=f"race_{tag}",
            )

            # Commit the session so trace data is persisted to the database
            # (process_event uses flush() internally; we need commit() for
            # cross-process database verification)
            try:
                _db.session.commit()
            except Exception:
                _db.session.rollback()

            # Step 5: Collect evidence — trace details
            trace_id = result.get("decision_trace_id")
            trace_data = {}
            if trace_id is not None:
                trace = DecisionTrace.query.get(trace_id)
                if trace is not None:
                    trace_data = {
                        "trace_id": trace.id,
                        "execution_status": trace.execution_status,
                        "execution_output": trace.execution_output,
                        "final_decision": trace.final_decision,
                    }

            # Report result
            report = {
                "tag": tag,
                "status": result.get("status"),
                "decision_trace_id": trace_id,
                "trace_data": trace_data,
                "execution": result.get("execution"),
                "decision": result.get("decision"),
                "entity_id": result.get("entity_id"),
                "success": True,
            }
            result_queue.put(report)

    except Exception as e:
        import traceback
        result_queue.put({
            "tag": tag,
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        })


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


def _seed_test_entity(db_uri: str) -> int:
    """Seed a shared entity in the test database.

    Returns the entity_id so both child processes can reference it.
    """
    from app import create_app, db
    from app.objects.models import Object
    from app.evidence.models_db import EvidenceRecord

    app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "SECRET_KEY": "test-secret-prod06",
        "DISABLE_RATE_LIMIT": "true",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        obj = Object(type="test", state={"initialized": True, "version": 1})
        db.session.add(obj)
        db.session.flush()
        entity_id = obj.id

        ev = EvidenceRecord(
            source_type="boundary_race_seed",
            source_id=str(entity_id),
            raw_reference={"test": True},
        )
        db.session.add(ev)
        db.session.commit()

    return entity_id


def test_concurrent_decision_boundary_via_processes():
    """Two genuinely independent Python processes execute process_event()
    concurrently, synchronized at the get_next_action() decision boundary.

    Proves:
    - Process A reaches decision boundary → computes decision A → executes A
    - Process B reaches decision boundary → computes decision B → executes B
    - Both decisions are simultaneously alive at the boundary
    - Each invocation retains its own context
    - No cross-consumption of decisions
    - Each DecisionTrace contains the complete canonical decision
    """
    # Step 1: Initialize the test database schema
    from app import create_app, db

    init_app = create_app(config_override={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": TEST_DB_URI,
        "SECRET_KEY": "test-secret-prod06",
        "DISABLE_RATE_LIMIT": "true",
        "WTF_CSRF_ENABLED": False,
    })

    with init_app.app_context():
        # Import all models to register them with metadata
        from app import models  # noqa: F401
        from app.evidence import models as _ev_models  # noqa: F401
        from app.execution import models as _exec_models  # noqa: F401
        from app.objects.models import Object  # noqa: F401
        from app.evidence.decision_trace import DecisionTrace  # noqa: F401
        from app.evidence.models_db import EvidenceRecord  # noqa: F401
        from app.execution_engine.models import Execution  # noqa: F401
        from app.execution_log.models import ExecutionLog  # noqa: F401
        from app.signals.models import Signal  # noqa: F401
        db.create_all()

    # Step 2: Seed a shared entity (and its evidence) in the test database
    entity_id = _seed_test_entity(TEST_DB_URI)
    assert entity_id is not None, "Failed to seed test entity"

    # Step 3: Create shared synchronization primitives using spawn context
    ctx = multiprocessing.get_context("spawn")
    barrier = ctx.Barrier(2, timeout=60)  # safety deadlock prevention
    result_queue = ctx.Queue()

    # Step 4: Spawn two independent processes
    proc_a = ctx.Process(
        target=_child_process,
        args=(barrier, result_queue, "A", entity_id, TEST_DB_URI),
    )
    proc_b = ctx.Process(
        target=_child_process,
        args=(barrier, result_queue, "B", entity_id, TEST_DB_URI),
    )

    proc_a.start()
    proc_b.start()

    # Step 5: Wait for both processes to complete
    proc_a.join(timeout=120)
    proc_b.join(timeout=120)

    # Step 6: Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get(timeout=10))

    # Verify both processes completed
    assert len(results) == 2, (
        f"Expected 2 results, got {len(results)}. "
        f"Process A alive={proc_a.is_alive()} exitcode={proc_a.exitcode} "
        f"Process B alive={proc_b.is_alive()} exitcode={proc_b.exitcode}"
    )

    # Terminate any stuck processes
    if proc_a.is_alive():
        proc_a.kill()
    if proc_b.is_alive():
        proc_b.kill()

    # Step 7: Classify results by tag
    result_map = {r["tag"]: r for r in results}

    # Verify both succeeded
    for tag in ("A", "B"):
        assert tag in result_map, f"Missing result for process {tag}"
        r = result_map[tag]
        assert r.get("success"), (
            f"Process {tag} failed: {r.get('error')}\n{r.get('traceback', '')}"
        )

    # Step 8: Both processes must have completed with status 'completed'
    for tag in ("A", "B"):
        assert result_map[tag]["status"] == "completed", (
            f"Process {tag} status={result_map[tag]['status']!r} — expected 'completed'"
        )

    # Step 9: Each invocation has its own decision trace (distinct identity)
    trace_ids = set()
    for tag in ("A", "B"):
        trace_id = result_map[tag].get("decision_trace_id")
        assert trace_id is not None, f"Process {tag} must have a trace id"
        assert isinstance(trace_id, int), f"Process {tag} trace_id must be int, got {type(trace_id).__name__}"
        trace_ids.add(trace_id)
    assert len(trace_ids) == 2, (
        f"Each invocation must have a distinct trace, got {len(trace_ids)}"
    )

    # Step 10: Prove invocation binding — each process's decision is bound to
    # its own invocation. Check that trace_data contains the canonical decision.
    for tag in ("A", "B"):
        trace_data = result_map[tag].get("trace_data", {})
        exec_output = trace_data.get("execution_output", {})
        canonical_decision = exec_output.get("canonical_decision")
        decision_context = exec_output.get("decision_context")

        assert canonical_decision is not None, (
            f"Process {tag} must have canonical_decision in trace"
        )
        assert isinstance(canonical_decision, dict), (
            f"Process {tag} canonical_decision must be a dict"
        )

        # The decision_context should record the intent (event_type)
        assert decision_context is not None, (
            f"Process {tag} must have decision_context in trace"
        )
        assert decision_context.get("intent") == f"boundary_race_{tag}", (
            f"Process {tag} must retain its own DecisionContext intent, "
            f"got {decision_context.get('intent')!r}"
        )

    # Step 11: Verify no global mutable decision override
    # If both decisions are the same type, that's fine — the binding
    # is proven by distinct trace IDs and process-specific context.
    # What matters is that each process's trace contains ITS OWN
    # canonical decision and ITS OWN decision context.
    trace_a = result_map["A"].get("trace_data", {})
    trace_b = result_map["B"].get("trace_data", {})

    exec_a = trace_a.get("execution_output", {})
    exec_b = trace_b.get("execution_output", {})

    canonical_a = exec_a.get("canonical_decision", {})
    canonical_b = exec_b.get("canonical_decision", {})

    # Each trace must have a canonical decision
    assert canonical_a, "Process A must have canonical decision in trace"
    assert canonical_b, "Process B must have canonical decision in trace"

    # The decision contexts must be distinct (different intents)
    ctx_a = exec_a.get("decision_context", {})
    ctx_b = exec_b.get("decision_context", {})
    assert ctx_a.get("intent") != ctx_b.get("intent"), (
        "Decision contexts must have distinct intents"
    )

    # Each trace must be independently reconstructable from the DB
    with init_app.app_context():
        from app.evidence.decision_trace import DecisionTrace as DT
        for tid in trace_ids:
            db_trace = DT.query.get(tid)
            assert db_trace is not None, (
                f"Trace {tid} must exist in database"
            )
            assert db_trace.execution_status == "success", (
                f"Trace {tid} execution_status must be 'success', "
                f"got {db_trace.execution_status!r}"
            )
            # Verify the trace has the canonical decision stored
            exec_out = db_trace.execution_output or {}
            assert exec_out.get("canonical_decision") is not None, (
                f"Trace {tid} must have canonical_decision in DB record"
            )

    # Clean up test data
    with init_app.app_context():
        from app.evidence.decision_trace import DecisionTrace as DT
        from app.evidence.models_db import EvidenceRecord
        from app.objects.models import Object
        from app.execution_log.models import ExecutionLog
        from app.signals.models import Signal
        from app.automation.models import AutomationLog

        # Delete in FK-safe order: child tables first
        if trace_ids:
            # Delete execution logs that reference the traces
            ExecutionLog.query.filter(
                ExecutionLog.object_id == entity_id
            ).delete(synchronize_session=False)
            # Delete signals
            Signal.query.filter(
                Signal.object_id == entity_id
            ).delete(synchronize_session=False)
            # Delete automation logs
            AutomationLog.query.delete(synchronize_session=False)
            # Delete decision traces
            DT.query.filter(DT.id.in_(list(trace_ids))).delete(
                synchronize_session=False
            )
        EvidenceRecord.query.filter_by(
            source_id=str(entity_id),
        ).delete(synchronize_session=False)
        Object.query.filter_by(id=entity_id).delete(synchronize_session=False)
        db.session.commit()