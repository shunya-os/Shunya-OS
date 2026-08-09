"""DB enforcement guard — ensures single source of truth for database access.

PHASE 3: All modules MUST use from app.core.db import db for database access.
Direct db.session usage outside core/ is forbidden.
"""


def forbid_direct_session_access():
    """Raise an exception if any module tries to create its own session.
    
    This is a marker function. The actual enforcement is by convention:
    all modules should import from app.core.db, not from app directly.
    """
    raise RuntimeError(
        "Direct database session access is forbidden. "
        "Use 'from app.core.db import db' instead of 'from app import db'."
    )