"""ZGC-PR-17C — Add durable memory fields to memory_records.

Additive migration: confidence, owner_identity_id, source columns on
memory_records — required by the MemoryEngine → MemoryRecord durable bridge.
Idempotent: safe to run multiple times.
"""

from sqlalchemy import text


def upgrade(engine):
    with engine.begin() as conn:
        inspector = __import__("sqlalchemy").inspect(engine)
        cols = [c["name"] for c in inspector.get_columns("memory_records")]
        if "confidence" not in cols:
            conn.execute(text("ALTER TABLE memory_records ADD COLUMN confidence FLOAT DEFAULT 1.0"))
        if "owner_identity_id" not in cols:
            conn.execute(text("ALTER TABLE memory_records ADD COLUMN owner_identity_id VARCHAR(64)"))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_mr_owner_identity ON memory_records(owner_identity_id)"
            ))
        if "source" not in cols:
            conn.execute(text("ALTER TABLE memory_records ADD COLUMN source VARCHAR(255)"))


def downgrade(engine):
    pass  # additive only — no destructive downgrade