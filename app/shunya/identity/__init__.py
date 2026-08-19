"""SHUNYA — Identity Engine (Phase D).

GATE 2.1 CONSOLIDATION: This module is being replaced by the canonical
kernel Identity contract (app/kernel/identity.py) and production
IdentityRepository (app/production/identity_repository.py).

The normalizer functions have been moved to core/identity/normalizers.py.
All new code should import from core.identity.normalizers.

engine.py, resolver.py, lifecycle.py, models.py are QUARANTINED — they
remain for backward compatibility only and are not the canonical identity
authority. They will be removed in a future consolidation pass.

Architectural authority: ES-010, SHUNYA_CORE_MODELS.md §3, Gate 2.1
"""

# Quarantined — kept for backward compat only
from app.shunya.identity.engine import IdentityEngine  # noqa: F401
from app.shunya.identity._legacy import IdentityResolver as _LegacyIdentityResolver  # noqa: F401
from app.shunya.identity.models import (  # noqa: F401
    Identity, ResolutionResult, ResolutionStatus,
    IdentityType, IdentityStatus, IdentityClaim,
)

# Normalizers migrated to core/identity/normalizers.py
# Re-exported here for backward compatibility
from core.identity.normalizers import normalize_email, normalize_phone, normalize_name  # noqa: F401

# Re-export legacy IdentityResolver for backward compatibility
# Phase 1 callers depend on the SQLAlchemy-based IdentityResolver(session=...) API
IdentityResolver = _LegacyIdentityResolver

__all__ = [
    "Identity", "ResolutionResult", "ResolutionStatus",
    "IdentityType", "IdentityStatus", "IdentityClaim",
    "IdentityEngine", "IdentityResolver",
    "normalize_email", "normalize_phone", "normalize_name",
]