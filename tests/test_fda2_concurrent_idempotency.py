"""FDA2 CORRECTION: Real concurrent idempotency test with file-backed SQLite.

This isolated test creates a Flask app with a temporary file-backed SQLite
database, then launches two concurrent threads that both call the real
IdempotencyGuard with the same source_type and source_id.

Proves:
- Exactly 1 processed=True, 1 skipped=True (behavioral proof)
- Exactly 1 durable evidence record in the database (DB-level proof)
- Uses the REAL IdempotencyGuard, REAL EvidenceRecord, REAL get_session()
"""

import os
import threading
import tempfile
import pytest


@pytest.fixture(scope="module")
def file_db():
    """Create a Flask app with a file-backed SQLite DB for concurrent testing."""
    from flask import Flask
    from app import db as _db
    from app.core.db import get_session
    from app.evidence.models_db import EvidenceRecord  # noqa: register model

    db_path = os.path.join(tempfile.gettempdir(), f"fda2_concurrent_{os.getpid()}.db")
    db_uri = f"sqlite:///{db_path}"

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "test"

    _db.init_app(app)

    with app.app_context():
        _db.create_all()

    yield app, db_path

    # Cleanup
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def clean_file_db(file_db):
    """Clean evidence_records between tests, keeping the file DB intact."""
    from app import db as _db
    from app.evidence.models_db import EvidenceRecord
    from app.core.db import get_session

    app, db_path = file_db
    with app.app_context():
        session = get_session()
        session.query(EvidenceRecord).delete()
        session.commit()
    yield
    with app.app_context():
        session = get_session()
        session.query(EvidenceRecord).delete()
        session.commit()


def test_concurrent_idempotency_atomicity(clean_file_db, file_db):
    """
    Two concurrent deliveries with the same source_type+source_id must produce:
    - exactly 2 results
    - exactly 1 processed=True
    - exactly 1 skipped=True
    - exactly 0 unexpected errors
    - exactly 1 durable evidence record in the database (verified by fresh connection)

    Uses the REAL IdempotencyGuard, REAL EvidenceRecord, REAL get_session(),
    and a file-backed SQLite database shared across threads.
    """
    from app.execution.idempotency import IdempotencyGuard
    from app.evidence.models_db import EvidenceRecord
    from app.core.db import get_session

    app, db_path = file_db

    guard = IdempotencyGuard()
    results = []
    errors = []
    lock = threading.Lock()

    # Unique test ID to avoid cross-test contamination
    test_id = "concurrent-atomic-proof"

    def deliver():
        """Thread worker: push app context, call real guard, collect result."""
        with app.app_context():
            try:
                r = guard.guard("concurrent", test_id, {"test": "atomic"})
                with lock:
                    results.append(r)
            except Exception as e:
                with lock:
                    errors.append(str(e))

    # Launch two threads simultaneously
    t1 = threading.Thread(target=deliver)
    t2 = threading.Thread(target=deliver)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # === BEHAVIORAL PROOF ===
    assert len(errors) == 0, f"Concurrent delivery errors: {errors}"
    assert len(results) == 2, f"Expected 2 results, got {len(results)}: {results}"

    processed = [r for r in results if r.get("processed") is True]
    skipped = [r for r in results if r.get("skipped") is True]
    idempotency_failed = [r for r in results if r.get("idempotency_check_failed") is True]

    assert len(idempotency_failed) == 0, f"Idempotency failures: {idempotency_failed}"
    assert len(processed) == 1, f"Expected 1 processed, got {len(processed)}: {results}"
    assert len(skipped) == 1, f"Expected 1 skipped, got {len(skipped)}: {results}"

    # === DURABLE EVIDENCE PROOF ===
    # Use a fresh SQLAlchemy connection (not the scoped session) to avoid
    # thread-local session visibility issues. The file-backed DB is shared
    # across all connections.
    from sqlalchemy import create_engine, text
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        row_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM evidence_records "
                "WHERE source_type='concurrent' AND source_id=:sid"
            ),
            {"sid": test_id},
        ).scalar()
    engine.dispose()

    assert row_count == 1, (
        f"Expected exactly 1 evidence record, found {row_count}. "
        "The DB unique constraint should have prevented the second insert."
    )