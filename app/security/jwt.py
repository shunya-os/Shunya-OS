"""SHUNYA OS — JWT Session Rotation (PyJWT).

Provides access and refresh token creation and verification
using the PyJWT library (HS256). Access tokens are short-lived
(15 minutes), refresh tokens are long-lived (7 days).

Usage:
    from app.security.jwt import (
        create_access_token, create_refresh_token, verify_token,
    )

    access = create_access_token("sid_abc123", "my-secret")
    payload = verify_token(access, "my-secret")
"""

from datetime import datetime, timedelta

import jwt


def create_access_token(identity_id: str, secret_key: str) -> str:
    """Create a short-lived (15 min) access token.

    Parameters
    ----------
    identity_id : str
        The subject identifier (e.g. ``sid_abc123``).
    secret_key : str
        The application secret key used for signing.

    Returns
    -------
    str
        A signed JWT access token.
    """
    return jwt.encode(
        {
            "sub": identity_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "type": "access",
        },
        secret_key,
        algorithm="HS256",
    )


def create_refresh_token(identity_id: str, secret_key: str) -> str:
    """Create a long-lived (7 day) refresh token.

    Parameters
    ----------
    identity_id : str
        The subject identifier.
    secret_key : str
        The application secret key.

    Returns
    -------
    str
        A signed JWT refresh token.
    """
    return jwt.encode(
        {
            "sub": identity_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=7),
            "type": "refresh",
        },
        secret_key,
        algorithm="HS256",
    )


def verify_token(token: str, secret_key: str) -> dict | None:
    """Verify and decode a JWT token.

    Parameters
    ----------
    token : str
        The JWT string to verify.
    secret_key : str
        The application secret key.

    Returns
    -------
    dict or None
        The decoded payload if valid, or ``None`` if the token is
        expired or otherwise invalid.
    """
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None