"""Pending multi-factor authentication transaction (G1.29).

The contract this module exists to enforce: **a TOTP is a second factor, never a
login**. Primary authentication (password) is the only thing that may open a
pending transaction, the transaction is bound to that user in the server-side
session, it expires after five minutes, it tolerates at most five code attempts,
and it is consumed exactly once.

Deliberately session-bound: the application already authenticates with a signed,
HttpOnly session cookie, so a pending transaction needs no parallel store, no
client-held token, and nothing the browser can forge or upgrade by supplying a
user id.
"""

from __future__ import annotations

import time
from typing import Optional

from flask import session

MFA_PENDING_USER_KEY = "mfa_pending_user_id"
MFA_PENDING_AT_KEY = "mfa_pending_at"
MFA_PENDING_ATTEMPTS_KEY = "mfa_pending_attempts"

#: A pending transaction is valid for five minutes after the password step.
MFA_PENDING_TTL_SECONDS = 5 * 60

#: Code attempts allowed inside one pending transaction.
MFA_MAX_ATTEMPTS = 5


def begin(user_id: int) -> None:
    """Open a pending transaction, discarding any prior session state.

    ``session.clear()`` is the important part: a half-authenticated session must
    never carry ``user_id``, ``identity_id`` or ``current_org_id`` into the
    challenge step, and a previous user's pending state must not survive.
    """
    session.clear()
    session[MFA_PENDING_USER_KEY] = int(user_id)
    session[MFA_PENDING_AT_KEY] = time.time()
    session[MFA_PENDING_ATTEMPTS_KEY] = 0


def clear() -> None:
    session.pop(MFA_PENDING_USER_KEY, None)
    session.pop(MFA_PENDING_AT_KEY, None)
    session.pop(MFA_PENDING_ATTEMPTS_KEY, None)


def pending_user_id() -> Optional[int]:
    """The user bound to a live pending transaction, or None.

    Expired or incomplete state is cleared as a side effect, so a stale
    transaction can never be resumed.
    """
    raw = session.get(MFA_PENDING_USER_KEY)
    started = session.get(MFA_PENDING_AT_KEY) or 0
    if not raw:
        return None
    try:
        user_id = int(raw)
        started_at = float(started)
    except (TypeError, ValueError):
        clear()
        return None
    if (time.time() - started_at) > MFA_PENDING_TTL_SECONDS:
        clear()
        return None
    return user_id


def register_failure() -> bool:
    """Record a wrong code. Returns False once the transaction is exhausted."""
    attempts = int(session.get(MFA_PENDING_ATTEMPTS_KEY) or 0) + 1
    session[MFA_PENDING_ATTEMPTS_KEY] = attempts
    if attempts >= MFA_MAX_ATTEMPTS:
        clear()
        return False
    return True


def consume() -> None:
    """Invalidate the transaction after successful completion (single use)."""
    clear()


def is_pending() -> bool:
    return pending_user_id() is not None
