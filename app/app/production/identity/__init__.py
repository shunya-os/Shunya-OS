"""SHUNYA — Identity & Organizations (Production).

Organization, workspace, user, team, invitation, and onboarding APIs.
"""

from flask import Blueprint

identity_bp = Blueprint("identity", __name__, url_prefix="/orgs")

from app.production.identity.org_routes import *  # noqa: F401, E402
from app.production.identity.workspace_routes import *  # noqa: F401, E402
from app.production.identity.user_routes import *  # noqa: F401, E402
from app.production.identity.invitation_routes import *  # noqa: F401, E402
from app.production.identity.switch_routes import *  # noqa: F401, E402
from app.production.identity.lifecycle_routes import *  # noqa: F401, E402
from app.production.identity.onboarding_routes import *  # noqa: F401, E402

__all__ = ["identity_bp"]