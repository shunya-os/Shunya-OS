"""Seed real data for awareness signal generation.

Creates 8 entities at various stages with realistic data,
unexecuted proposals, stale entities, and evidence logs.

Run: python3 scripts/seed_data.py
"""

import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql://shunya:***@localhost:5432/shunya_db")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
os.environ["DISABLE_RATE_LIMIT"] = "true"


def seed():
    """Seed real data for awareness signal generation.
    
    WARNING: SQLite in-memory databases create a NEW database per connection.
    Use a persistent database (PostgreSQL or file-based SQLite) for validation.
    
    Example:
        DATABASE_URL=sqlite:///shunya_test.db python3 scripts/seed_data.py
        DATABASE_URL=postgresql://user:pass@localhost/shunya python3 scripts/seed_data.py
    """
    import warnings
    if os.environ.get("DATABASE_URL", "").startswith("sqlite:///:memory:"):
        warnings.warn(
            "SQLite in-memory database detected. Awareness/decision APIs will NOT "
            "see seeded data due to connection isolation. Use a persistent database "
            "(e.g., DATABASE_URL=sqlite:///shunya_test.db) for validation."
        )
    
    from app import create_app, db

    app = create_app()

    with app.app_context():
        db.create_all()

        from app.objects.models import Object
        from app.communication.models import MessageProposal
        from app.execution_log.models import ExecutionLog, log_execution

        # ── Clear existing test data ──
        ExecutionLog.query.delete()
        MessageProposal.query.delete()
        Object.query.delete()
        db.session.commit()

        # ── 1. Create entities at various stages ──
        now = datetime.now(timezone.utc)

        entities = [
            Object(
                object_type="lead",
                state={
                    "name": "Rahul Sharma",
                    "stage": "new",
                    "phone": "+919876543210",
                    "email": "rahul@example.com",
                    "deal_value": 50000,
                    "currency": "INR",
                },
                created_at=now - timedelta(hours=8),
                updated_at=now - timedelta(hours=8),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Priya Patel",
                    "stage": "new",
                    "phone": "+919876543211",
                    "email": "priya@example.com",
                },
                created_at=now - timedelta(hours=6),
                updated_at=now - timedelta(hours=6),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Amit Gupta",
                    "stage": "contacted",
                    "phone": "+919876543212",
                    "email": "amit@example.com",
                },
                created_at=now - timedelta(hours=48),
                updated_at=now - timedelta(hours=24),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Sneha Reddy",
                    "stage": "contacted",
                    "phone": "+919876543213",
                    "email": "sneha@example.com",
                    "deal_value": 25000,
                    "currency": "INR",
                },
                created_at=now - timedelta(hours=72),
                updated_at=now - timedelta(hours=48),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Vikram Singh",
                    "stage": "quoted",
                    "phone": "+919876543214",
                    "email": "vikram@example.com",
                    "deal_value": 150000,
                    "currency": "INR",
                },
                created_at=now - timedelta(hours=96),
                updated_at=now - timedelta(hours=72),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Ananya Joshi",
                    "stage": "quoted",
                    "phone": "+919876543215",
                    "email": "ananya@example.com",
                    "deal_value": 75000,
                    "currency": "INR",
                },
                created_at=now - timedelta(hours=120),
                updated_at=now - timedelta(hours=96),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Arjun Mehta",
                    "stage": "quoted",
                    "phone": "+919876543216",
                    "email": "arjun@example.com",
                    "deal_value": 100000,
                    "currency": "INR",
                },
                created_at=now - timedelta(hours=168),
                updated_at=now - timedelta(hours=120),
            ),
            Object(
                object_type="lead",
                state={
                    "name": "Divya Kumar",
                    "stage": "closed",
                    "phone": "+919876543217",
                    "email": "divya@example.com",
                    "deal_value": 30000,
                    "currency": "INR",
                },
                created_at=now - timedelta(hours=240),
                updated_at=now - timedelta(hours=48),
            ),
        ]

        for e in entities:
            db.session.add(e)
        db.session.flush()

        # ── 2. Create pending proposals (unexecuted >1h) ──
        proposals = [
            MessageProposal(
                to="rahul@example.com",
                message="Hi Rahul, welcome to Panchi Club! Let's plan your Bali trip.",
                entity_id=entities[0].id,
                entity_name="Rahul Sharma",
                status="pending",
                context_reason="New lead — no quote sent",
                context_source="effect_engine",
                context_confidence="high",
                created_at=now - timedelta(hours=4),
            ),
            MessageProposal(
                to="amit@example.com",
                message="Hi Amit, here is your custom quote for the Kerala package.",
                entity_id=entities[2].id,
                entity_name="Amit Gupta",
                status="pending",
                context_reason="Lead contacted but not quoted",
                context_source="effect_engine",
                context_confidence="high",
                created_at=now - timedelta(hours=3),
            ),
            MessageProposal(
                to="vikram@example.com",
                message="Hi Vikram, just following up on your Dubai itinerary quote.",
                entity_id=entities[4].id,
                entity_name="Vikram Singh",
                status="pending",
                context_reason="Quote sent but no response",
                context_source="effect_engine",
                context_confidence="high",
                created_at=now - timedelta(hours=6),
            ),
            MessageProposal(
                to="ananya@example.com",
                message="Hi Ananya, special discount on our Rajasthan tour this month!",
                entity_id=entities[5].id,
                entity_name="Ananya Joshi",
                status="pending",
                context_reason="Follow-up after quote",
                context_source="effect_engine",
                context_confidence="medium",
                created_at=now - timedelta(hours=12),
            ),
            MessageProposal(
                to="arjun@example.com",
                message="Hi Arjun, your Kashmir package is ready for confirmation.",
                entity_id=entities[6].id,
                entity_name="Arjun Mehta",
                status="pending",
                context_reason="Quote ready for approval",
                context_source="effect_engine",
                context_confidence="high",
                created_at=now - timedelta(hours=24),
            ),
        ]

        for p in proposals:
            db.session.add(p)
        db.session.flush()

        # ── 3. Insert evidence logs (execution_summary, proposals, AI) ──
        # Recent successful cycle
        log_execution(0, "EVIDENCE", {
            "type": "execution_summary",
            "data": {"actions_taken": 3, "noops": 5, "errors": 0, "status": "completed"},
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
        })
        # Failed cycle
        log_execution(0, "EVIDENCE", {
            "type": "execution_summary",
            "data": {"actions_taken": 0, "noops": 2, "errors": 4, "status": "partial"},
            "timestamp": (now - timedelta(hours=2)).isoformat(),
        })
        # Another successful cycle
        log_execution(0, "EVIDENCE", {
            "type": "execution_summary",
            "data": {"actions_taken": 1, "noops": 8, "status": "completed"},
            "timestamp": (now - timedelta(hours=4)).isoformat(),
        })
        # AI fallback evidence
        log_execution(0, "EVIDENCE", {
            "type": "ai",
            "data": {"provider": "gemini", "model": "gemini-2.0-flash", "confidence": 0.65, "fallback_used": True},
            "timestamp": (now - timedelta(hours=1)).isoformat(),
        })
        log_execution(0, "EVIDENCE", {
            "type": "ai",
            "data": {"provider": "openrouter", "model": "deepseek-chat", "confidence": 0.5, "fallback_used": True},
            "timestamp": (now - timedelta(hours=2)).isoformat(),
        })
        log_execution(0, "EVIDENCE", {
            "type": "ai",
            "data": {"provider": "local", "model": "local", "confidence": 0.35, "fallback_used": True},
            "timestamp": (now - timedelta(hours=3)).isoformat(),
        })

        db.session.commit()

        # ── 4. Summary ──
        print(f"Seeded {len(entities)} entities")
        print(f"Seeded {len(proposals)} pending proposals")
        for e in entities:
            st = e.state or {}
            upd = e.updated_at
            if upd:
                if upd.tzinfo is None:
                    from datetime import timezone as tz
                    upd = upd.replace(tzinfo=tz.utc)
                age = f"{int((datetime.now(timezone.utc) - upd).total_seconds()/3600)}h ago"
            else:
                age = "never"
            print(f"  Entity #{e.id}: {st.get('name','?')} — stage={st.get('stage','?')} updated={age}")
        print(f"Seeded 6 evidence logs (3 execution, 3 AI)")
        print("\nSeed complete. Now run awareness scan to verify signals.")


if __name__ == "__main__":
    seed()