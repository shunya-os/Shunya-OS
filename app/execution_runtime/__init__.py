"""Compatibility stub for archived execution_runtime.

The execution_runtime module was migrated to app/execution/ and
app/execution_engine/. This stub exists only to maintain the
canonical ownership contract defined in CANONICAL_ARCHITECTURE.yaml.

Imports the canonical execution components from their current locations.
"""

from app.execution import __init__ as execution_module  # noqa: F401
from app.execution_engine import routes  # noqa: F401