"""SHUNYA — Identity normalizer (Phase D).

GATE 2.1 CONSOLIDATION: These functions have been moved to
core/identity/normalizers.py as the canonical location.

This file now re-exports from core for backward compatibility.
New code should import from core.identity.normalizers directly.

Architectural authority: ES-010 (superseded by Gate 2.1)
"""

from core.identity.normalizers import (  # noqa: F401
    normalize_email,
    normalize_phone,
    normalize_name,
    normalize_for_type,
    identity_type_strength,
)


__all__ = [
    "normalize_email",
    "normalize_phone",
    "normalize_name",
    "normalize_for_type",
    "identity_type_strength",
]