"""R6B-2.5 — canonical bootstrap probe.

Runs the application's own initialization path (app/__init__.py:
db.create_all() + default workspace seeding) against whatever
DATABASE_URL points at. Prints the observed schema state. No schema
mutation of its own — this is exactly the production boot path.
"""
import os
import sys

# Resolve the repository root the same way migrations/env.py does, so this
# script runs from the repository root with no PYTHONPATH override.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text


def main() -> int:
    from app import create_app, db

    app = create_app(config_override={
        "TESTING": True,
        "DISABLE_RATE_LIMIT": "true",
        "SECRET_KEY": "r6b25-bootstrap",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        print("dialect:", db.engine.dialect.name)
        print("server_version:", db.session.execute(
            text("SHOW server_version")).scalar())
        print("database:", db.session.execute(
            text("SELECT current_database()")).scalar())
        n_tables = db.session.execute(text(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='public'")).scalar()
        print("tables_after_create_all:", n_tables)
    return 0


if __name__ == "__main__":
    sys.exit(main())
