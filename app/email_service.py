"""
SHUNYA Email Service — notification delivery for verification, reset, onboarding.

Architecture:
  - Uses email_core.py (canonical send path) which checks is_human_triggered=True
  - Creates durable EmailRecord for every send attempt
  - In production: sends via Resend when EMAIL_PROVIDER=resend + RESEND_API_KEY set
  - Falls back to logging when unconfigured

  Required env vars for production delivery:
    EMAIL_PROVIDER=resend
    RESEND_API_KEY=<production-key>  (set by founder on production machine)
    RESEND_FROM=SHUNYA <hello@shunyaos.com>
    SHUNYA_BASE_URL=https://shunyaos.com

All email rendering uses plain-text templates.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("SHUNYA_BASE_URL", os.environ.get("PUBLIC_URL", "http://127.0.0.1:5001"))


def send_email(
    to: str,
    subject: str,
    body: str,
    notification_type: str = "notify",
    business_event_id: str = None,
    category: str = "operational",
    tenant_id: int = None,
    identity_id: str = None,
) -> dict:
    """Send an email via the canonical email_core path.

    Creates a durable EmailRecord with full lifecycle tracking.

    Returns the full result dict from email_core.send() including:
      status (accepted|logged|failed|blocked|exhausted|unconfigured)
      record_id
      provider_id (when available)
    """
    from app.communication.email_core import send as core_send

    # Generate business_event_id if not provided
    if not business_event_id:
        import uuid
        business_event_id = f"{notification_type}:{uuid.uuid4().hex[:16]}"

    result = core_send(
        recipient=to,
        subject=subject,
        body=body,
        notification_type=notification_type,
        business_event_id=business_event_id,
        category=category,
        tenant_id=tenant_id,
        identity_id=identity_id,
        is_human_triggered=True,
    )
    return result


# ── Template Builders ──────────────────────────────────────────────────


def build_verification_email(to: str, token: str) -> tuple:
    """Build verification email. Returns (subject, body)."""
    verify_url = f"{BASE_URL}/auth/verify-email?token={token}"
    subject = "Verify your SHUNYA email address"
    body = f"""Hello,

Thank you for creating your SHUNYA account.

To verify your email address and activate your workspace, click the link below:

{verify_url}

This link expires in 24 hours and can only be used once.

If you did not create a SHUNYA account, please ignore this email.

— SHUNYA
"""
    return subject, body


def build_reset_email(to: str, token: str) -> tuple:
    """Build password reset email. Returns (subject, body)."""
    reset_url = f"{BASE_URL}/auth/reset-password?token={token}"
    subject = "Reset your SHUNYA password"
    body = f"""Hello,

A password reset was requested for your SHUNYA account.

To reset your password, click the link below:

{reset_url}

This link expires in 1 hour and can only be used once.

If you did not request this reset, please ignore this email. Your password will remain unchanged.

— SHUNYA
"""
    return subject, body


def build_onboarding_complete_email(email: str, workspace_name: str) -> tuple:
    """Build onboarding completion confirmation. Returns (subject, body)."""
    subject = "Your SHUNYA is ready"
    body = f"""Hello,

Your SHUNYA workspace is ready.

Workspace: {workspace_name}

You can now access SHUNYA at:
{BASE_URL}

Your workspace includes:
- AI-powered conversations and memory
- Personal tasks, files, and knowledge
- Finance, outputs, and reports
- Full SHUNYA intelligence

If you need help getting started, visit:
{BASE_URL}/support

— SHUNYA
"""
    return subject, body