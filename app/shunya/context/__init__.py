"""SHUNYA — Context Fusion Engine package (Phase E).

Canonical context assembly from Identity Engine, Knowledge Store,
and request metadata. Deterministic. Budget-enforced. Fingerprinted.

Architectural authority: ES-009
"""

from . import models
from . import engine
from . import assembly
from . import providers
from . import budget
from . import fingerprint

__all__ = [
    "models",
    "engine",
    "assembly",
    "providers",
    "budget",
    "fingerprint",
]