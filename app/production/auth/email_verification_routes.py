"""DEPRECATED — duplicate email-verification routes (retired, not implemented here).

This module previously registered raw-token routes directly on ``auth_bp``:

    POST /request-verification      (created an EmailVerificationToken, claimed
                                     "a verification link has been sent", but
                                     NEVER called send_email and leaked the raw
                                     token in the response body)
    GET  /verify-email/<token>      (set EmailVerificationToken.verified=True
                                     but NEVER set TeamMember.verified)

Both were fake claimed-success paths duplicate to the canonical, rate-limited
flow in ``app/auth_routes.py``:

    POST /api/v1/auth/request-verification  -> api_request_verification()
    POST /api/v1/auth/verify-email          -> api_verify_email() (sets
                                               TeamMember.verified=True and
                                               creates the personal workspace)

The SPA calls only the canonical ``/api/v1/auth/*`` endpoints (via
frontend/src/api/client.ts BASE=/api/v1 and the auth components), so these
unprefixed duplicates were unreachable from the product and have been
removed. The EmailVerificationToken model remains defined in app/auth.py
(no migration needed; unused rows are inert).

Module body is intentionally empty — it is still imported for registration
side effects in ``app/__init__.py`` / ``app/production/auth/__init__.py`` and
must stay importable.
"""