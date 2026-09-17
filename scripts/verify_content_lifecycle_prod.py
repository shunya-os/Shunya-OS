#!/usr/bin/env python3
"""Read-only proof: does the production DB support the ContentGeneration lifecycle model?

Runs the ORM query the API endpoint uses, against the LIVE production database.
No writes. Prints columns + query outcome.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError, OperationalError


def main() -> int:
    os.environ.setdefault("SHUNYA_ENVIRONMENT", "production")
    from app import create_app, db

    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        cols = [c["name"] for c in insp.get_columns("m6_content_generations")]
        print("LIVE COLUMNS:", cols)
        model_cols = [c.name for c in
                      __import__("app.integration.models", fromlist=["ContentGeneration"])
                      .ContentGeneration.__table__.columns]
        print("MODEL COLUMNS:", model_cols)
        missing = [c for c in model_cols if c not in cols]
        print("MISSING IN DB:", missing)

        # The exact query shape the endpoint performs.
        try:
            rows = db.session.execute(
                text("SELECT id, status, is_deleted FROM m6_content_generations LIMIT 1")
            ).fetchall()
            print("ENDPOINT_QUERY: OK rows=", len(rows))
        except (ProgrammingError, OperationalError) as exc:
            print("ENDPOINT_QUERY: FAILED ->", type(exc).__name__)
            print(str(exc)[:300])

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
