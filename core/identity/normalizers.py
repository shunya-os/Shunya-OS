"""SHUNYA Core — Identity Normalizers.

Canonical identity normalization functions extracted from
app/shunya/identity/normalizer.py (which was a duplicate of the
kernel identity architecture).

Architectural authority: Gate 2.1 Identity Consolidation
"""

from __future__ import annotations

import re
from typing import Optional


def normalize_email(email: str) -> str:
    """Lowercase, strip whitespace."""
    return email.strip().lower() if email else ""


def normalize_phone(phone: str) -> str:
    """Normalize to E.164 format: strip non-digits, keep leading +."""
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    digits = re.sub(r"[^\d]", "", cleaned)
    if cleaned.startswith("+"):
        return "+" + digits
    return digits


def normalize_name(name: str) -> str:
    """Strip extra whitespace, title case."""
    if not name:
        return ""
    return " ".join(name.strip().title().split())


def normalize_for_type(identity_type: str, value: str) -> str:
    """Route normalization by identity type."""
    if identity_type == "email":
        return normalize_email(value)
    if identity_type == "phone":
        return normalize_phone(value)
    if identity_type.startswith("channel:"):
        return value.strip()
    if identity_type in ("document_id", "external_id", "alias"):
        return value.strip()
    return value.strip()


def identity_type_strength(identity_type: str) -> str:
    """Return the strength classification of an identity type.

    Returns 'strong', 'medium', or 'weak' per Core Models §3.
    """
    strong = {"email", "phone", "channel:whatsapp", "channel:telegram", "document_id"}
    medium = {"external_id"}
    if identity_type in strong:
        return "strong"
    if identity_type in medium:
        return "medium"
    return "weak"


__all__ = [
    "normalize_email",
    "normalize_phone",
    "normalize_name",
    "normalize_for_type",
    "identity_type_strength",
]