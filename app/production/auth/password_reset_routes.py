"""DEPRECATED — duplicate password-reset routes (retired, not implemented here).

This module previously registered raw-token routes directly on ``auth_bp``:

    POST /forgot-password            (created a PasswordResetToken, claimed
                                      "a reset link has been sent", but NEVER
                                      called send_email and leaked the raw
                                      ``_reset_token`` in the response body —
                                      a security issue)
    GET/POST /reset-password/<token> (token in URL path, no rate limiting)

These were fake claimed-success paths duplicate to the canonical, rate-limited
flow in ``app/auth_routes.py``:

    POST /api/v1/auth/forgot-password -> api_forgot_password() (sends the real
                                         email via build_reset_email + send_email,
                                         never returns the token)
    POST /api/v1/auth/reset-password  -> api_reset_password() (token in body,
                                         invalidates used tokens, logs out sessions)

The SPA calls only the canonical ``/api/v1/auth/*`` endpoints (via
frontend/src/api/client.ts BASE=/api/v1 and the auth components), so these
unprefixed duplicates were unreachable from the product and have been
removed. The PasswordResetToken model remains owned by the canonical flow.

Module body is intentionally empty — it is still imported for registration
side effects in ``app/__init__.py`` / ``app/production/auth/__init__.py`` and
must stay importable.
"""