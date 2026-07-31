"""SHUNYA — Production Auth Services (Milestone X, D2).

Registers auth routes on the existing auth_bp blueprint:
  - Password reset
  - Email verification
  - MFA / 2FA
  - Session revocation & device management
"""

# Importing these modules registers their routes on auth_bp
from app.production.auth import (
    email_verification_routes,  # noqa: F401
    mfa_routes,  # noqa: F401
    password_change_routes,  # noqa: F401
    password_reset_routes,  # noqa: F401
    session_routes,  # noqa: F401
)
