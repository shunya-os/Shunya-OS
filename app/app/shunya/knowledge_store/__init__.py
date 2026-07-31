"""SHUNYA — Knowledge Store package (Phase C).

Immutable, versioned, business-agnostic knowledge foundation.

Architectural authority: Phase C — Knowledge Store Foundation
"""

import importlib.util
import os
import sys

# Load the legacy knowledge_store module to re-export ImmutableKnowledgeStore
# and KnowledgeFact for backward compatibility (the package shadows the module).
_legacy_name = "app.shunya.knowledge_store_legacy"
_legacy_path = os.path.join(os.path.dirname(__file__), "..", "knowledge_store.py")
_spec = importlib.util.spec_from_file_location(_legacy_name, _legacy_path)
_legacy = importlib.util.module_from_spec(_spec)
sys.modules[_legacy_name] = _legacy
_spec.loader.exec_module(_legacy)

ImmutableKnowledgeStore = _legacy.ImmutableKnowledgeStore
KnowledgeFact = _legacy.KnowledgeFact

from . import models
from . import store
from . import repository
from . import versioning

__all__ = [
    "models",
    "store",
    "repository",
    "versioning",
    "ImmutableKnowledgeStore",
    "KnowledgeFact",
]