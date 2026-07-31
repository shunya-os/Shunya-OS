"""SHUNYA — Context fingerprinting (Phase E).

Deterministic fingerprints for caching, traceability, and audit.
Not for reasoning.

Architectural authority: ES-009
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


class Fingerprinter:
    """Generates deterministic fingerprints for context data.

    Identical context data always produces identical fingerprints.
    """

    def __init__(self, algorithm: str = "sha256") -> None:
        self._algorithm = algorithm

    def fingerprint(
        self,
        sections: Dict[str, List[Dict[str, Any]]],
        tenant_id: int,
        actor_id: str,
        purpose_code: str,
    ) -> str:
        """Generate a deterministic fingerprint for a context assembly.

        Args:
            sections: Provider sections and their items.
            tenant_id: The owning tenant.
            actor_id: The requesting actor.
            purpose_code: The purpose classification.

        Returns:
            A hex-encoded fingerprint string.
        """
        # Build a canonical representation
        canonical: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "purpose_code": purpose_code,
            "sections": {},
        }

        for provider_name in sorted(sections.keys()):
            items = sections.get(provider_name, [])
            # Sort items by their content for deterministic ordering
            sorted_items = sorted(items, key=lambda i: json.dumps(i, sort_keys=True, default=str))
            canonical["sections"][provider_name] = sorted_items

        # Serialize with sorted keys for deterministic output
        serialized = json.dumps(canonical, sort_keys=True, default=str)
        h = hashlib.new(self._algorithm)
        h.update(serialized.encode("utf-8"))
        return h.hexdigest()

    def fingerprint_section(self, section_name: str, items: List[Dict[str, Any]]) -> str:
        """Generate a fingerprint for a single section."""
        serialized = json.dumps(
            {"section": section_name, "items": sorted(items, key=lambda i: json.dumps(i, sort_keys=True, default=str))},
            sort_keys=True, default=str,
        )
        h = hashlib.new(self._algorithm)
        h.update(serialized.encode("utf-8"))
        return h.hexdigest()