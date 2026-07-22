"""SHUNYA — Identity Engine (Phase D).

Canonical identity resolution with persistent storage via Knowledge Store.
Deterministic, never silently merges, tenant-isolated.

Architectural authority: ES-010, SHUNYA_CORE_MODELS.md §3
"""

from app.shunya.identity.models import (
    Identity, ResolutionResult, ResolutionStatus,
    IdentityType, IdentityStatus, IdentityClaim,
)
from app.shunya.identity.engine import IdentityEngine
from app.shunya.identity.normalizer import normalize_email, normalize_phone, normalize_name
from app.shunya.identity._legacy import IdentityResolver as _LegacyIdentityResolver

# Re-export legacy IdentityResolver for backward compatibility
# Phase 1 callers depend on the SQLAlchemy-based IdentityResolver(session=...) API
IdentityResolver = _LegacyIdentityResolver

__all__ = [
    "Identity", "ResolutionResult", "ResolutionStatus",
    "IdentityType", "IdentityStatus", "IdentityClaim",
    "IdentityEngine", "IdentityResolver",
    "normalize_email", "normalize_phone", "normalize_name",
]