"""SHUNYA — Context providers (Phase E).

Provider abstractions for Identity, Knowledge, and Request data.
The Context Fusion Engine orchestrates providers rather than embedding
retrieval logic.

Architectural authority: ES-009
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.shunya.context.models import ContextRequest, ContextSection


class ContextProvider(ABC):
    """Abstract provider for context data."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def fetch(self, request: ContextRequest) -> ContextSection:
        """Fetch context data for the given request.

        Returns a ContextSection. If the provider is unavailable,
        returns a degraded section with an exclusion_reason.
        """


class IdentityContextProvider(ContextProvider):
    """Provides identity data for the context.

    Resolves the actor's identity, subject identity, and any
    related identities via the Identity Engine.
    """

    def __init__(self, identity_engine: Any) -> None:
        self._engine = identity_engine

    def name(self) -> str:
        return "identity"

    def fetch(self, request: ContextRequest) -> ContextSection:
        start = time.time()
        try:
            items: List[Dict[str, Any]] = []

            # Resolve actor identity
            from app.shunya.identity.models import IdentityClaim
            result = self._engine.resolve(IdentityClaim(
                identity_type="alias",
                identity_value=request.actor_id,
                tenant_id=request.tenant_id,
            ))
            if result.identity:
                items.append({
                    "type": "actor_identity",
                    "identity_id": result.identity.identity_id,
                    "person_id": result.identity.person_id,
                    "confidence": result.confidence,
                    "status": result.identity.status,
                })

            # Subject identity (if different from actor)
            if request.subject_id and request.subject_id != request.actor_id:
                subject_result = self._engine.resolve(IdentityClaim(
                    identity_type="alias",
                    identity_value=request.subject_id,
                    tenant_id=request.tenant_id,
                ))
                if subject_result.identity:
                    items.append({
                        "type": "subject_identity",
                        "identity_id": subject_result.identity.identity_id,
                        "person_id": subject_result.identity.person_id,
                        "confidence": subject_result.confidence,
                        "status": subject_result.identity.status,
                    })

            elapsed = (time.time() - start) * 1000
            return ContextSection(
                provider=self.name(),
                items=items,
                elapsed_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ContextSection(
                provider=self.name(),
                is_degraded=True,
                exclusion_reason=f"Identity provider error: {e}",
                elapsed_ms=elapsed,
            )


class KnowledgeContextProvider(ContextProvider):
    """Provides knowledge data for the context.

    Retrieves relevant knowledge facts from the Knowledge Store
    scoped to the tenant.
    """

    def __init__(self, knowledge_store: Any) -> None:
        self._ks = knowledge_store

    def name(self) -> str:
        return "knowledge"

    def fetch(self, request: ContextRequest) -> ContextSection:
        start = time.time()
        try:
            from app.shunya.knowledge_store.models import SearchQuery, SearchFilter

            items: List[Dict[str, Any]] = []

            # Query knowledge relevant to the tenant
            query = SearchQuery(
                namespace=f"identity:{request.tenant_id}",
                limit=50,
            )
            result = self._ks.search(query)
            for obj in result.items:
                items.append({
                    "object_id": obj.object_id,
                    "key": obj.key,
                    "type": obj.type,
                    "namespace": obj.namespace,
                    "version": obj.version,
                    "status": obj.status,
                })

            elapsed = (time.time() - start) * 1000
            return ContextSection(
                provider=self.name(),
                items=items,
                elapsed_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ContextSection(
                provider=self.name(),
                is_degraded=True,
                exclusion_reason=f"Knowledge provider error: {e}",
                elapsed_ms=elapsed,
            )


class RequestContextProvider(ContextProvider):
    """Provides request-level metadata for the context.

    Includes the original request parameters, session information,
    and tenant configuration.
    """

    def __init__(self) -> None:
        pass

    def name(self) -> str:
        return "request"

    def fetch(self, request: ContextRequest) -> ContextSection:
        start = time.time()
        try:
            items: List[Dict[str, Any]] = [
                {
                    "type": "request_metadata",
                    "tenant_id": request.tenant_id,
                    "actor_id": request.actor_id,
                    "purpose_code": request.purpose_code,
                    "subject_id": request.subject_id,
                    "max_items": request.max_items,
                    "max_size_bytes": request.max_size_bytes,
                    "timeout_ms": request.timeout_ms,
                },
                {
                    "type": "session_context",
                    "request_id": request.request_id or "",
                    "correlation_id": request.correlation_id or "",
                },
            ]

            elapsed = (time.time() - start) * 1000
            return ContextSection(
                provider=self.name(),
                items=items,
                elapsed_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ContextSection(
                provider=self.name(),
                is_degraded=True,
                exclusion_reason=f"Request provider error: {e}",
                elapsed_ms=elapsed,
            )