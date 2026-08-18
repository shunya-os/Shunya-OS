"""Execution Engine routes — PROD-06: removed.

The POST /api/v1/execution/<id>/run route was removed in PROD-06 because
it constituted a second execution authority. All execution goes through
the canonical path:

    runtime/entry.py process_event()
      → gate
      → run_cycle()
      → get_next_action()
      → execute_action() (gate-checked)

No HTTP-initiated execution bypass is permitted.
"""

from flask import Blueprint

execution_bp = Blueprint("execution_engine", __name__, url_prefix="/api/v1/execution")
# No routes — the /run route was removed in PROD-06.
# Kept the Blueprint to avoid breaking tests that import execution_bp.