"""SHUNYA — Identity Engine (Phase D).

GATE 2.1 CONSOLIDATION: QUARANTINED — This is a duplicate of the canonical
kernel Identity contract (app/kernel/identity.py) and the production
IdentityRepository (app/production/identity_repository.py).

This module persists via Knowledge Store, which is a non-canonical path.
The canonical persistence path is via IdentityRepository using the
shunya_identities + persons database tables.

Kept for backward compatibility only. Will be removed when all consumers
have migrated to the kernel Identity contract.

Architectural authority: ES-010 (superseded by Gate 2.1 canonical rule)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.shunya.identity.models import (
    Identity, IdentityClaim, ResolutionResult, ResolutionStatus,
    IdentityStatus, IdentityType,
)
from app.shunya.identity.resolver import IdentityResolver
from app.shunya.identity.lifecycle import LifecycleEngine
from app.shunya.identity.normalizer import normalize_for_type


class IdentityEngine:
    """Identity Engine — canonical identity resolution and management.

    Integrates:
      - IdentityResolver (lookup, register, merge)
      - LifecycleEngine (state transitions)
      - Knowledge Store (persistence)
      - Event Bus (event publishing)
      - Metrics, Logging, Health
    """

    def __init__(
        self,
        knowledge_store: Any,
        resolver: Optional[IdentityResolver] = None,
        lifecycle: Optional[LifecycleEngine] = None,
        logger: Any = None,
        metrics_registry: Any = None,
        health_registry: Any = None,
        event_bus: Any = None,
    ) -> None:
        self._ks = knowledge_store
        self._resolver = resolver or IdentityResolver(knowledge_store)
        self._lifecycle = lifecycle or LifecycleEngine()
        self._logger = logger
        self._metrics = metrics_registry
        self._health = health_registry
        self._event_bus = event_bus

        # Metrics
        if self._metrics:
            self._resolve_counter = self._metrics.counter(
                "identity_resolutions_total", "Identity resolution attempts"
            )
            self._register_counter = self._metrics.counter(
                "identity_registrations_total", "Identity registrations"
            )
            self._match_counter = self._metrics.counter(
                "identity_matches_total", "Successful identity matches"
            )
            self._ambig_counter = self._metrics.counter(
                "identity_ambiguous_total", "Ambiguous identity resolutions"
            )

        # Health
        if self._health:
            self._health.register("identity_engine", self._health_check)

    # ---- Resolve -----------------------------------------------------------

    def resolve(self, claim: IdentityClaim) -> ResolutionResult:
        """Resolve an identity claim."""
        start = time.time()
        result = self._resolver.resolve(claim)
        self._record_metrics("resolve", start, result)
        return result

    def resolve_by_email(self, email: str, tenant_id: int) -> ResolutionResult:
        return self._resolver.resolve_by_email(email, tenant_id)

    def resolve_by_phone(self, phone: str, tenant_id: int) -> ResolutionResult:
        return self._resolver.resolve_by_phone(phone, tenant_id)

    def resolve_by_channel(self, channel: str, channel_id: str, tenant_id: int) -> ResolutionResult:
        return self._resolver.resolve_by_channel(channel, channel_id, tenant_id)

    def resolve_multi(
        self,
        email: str = "",
        phone: str = "",
        channel: str = "",
        channel_id: str = "",
        tenant_id: int = 0,
    ) -> ResolutionResult:
        return self._resolver.resolve_multi(
            email=email, phone=phone,
            channel=channel, channel_id=channel_id,
            tenant_id=tenant_id,
        )

    # ---- Register ----------------------------------------------------------

    def register(
        self,
        identity_type: str,
        identity_value: str,
        tenant_id: int,
        person_id: str = "",
        verification_state: str = "unverified",
        confidence: float = 0.5,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Optional[Identity]:
        """Register a new identity.

        Returns None if the identity already exists (duplicate).
        """
        identity = self._resolver.register(
            identity_type=identity_type,
            identity_value=identity_value,
            tenant_id=tenant_id,
            person_id=person_id,
            verification_state=verification_state,
            confidence=confidence,
            provenance=provenance,
        )
        if identity:
            self._emit_event("identity.created", identity)
            if self._metrics:
                self._register_counter.inc()
        return identity

    def register_with_person(
        self,
        identity_type: str,
        identity_value: str,
        tenant_id: int,
        person_id: str,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Identity:
        identity = self._resolver.register_with_person(
            identity_type=identity_type,
            identity_value=identity_value,
            tenant_id=tenant_id,
            person_id=person_id,
            provenance=provenance,
        )
        self._emit_event("identity.created", identity)
        if self._metrics:
            self._register_counter.inc()
        return identity

    # ---- Lifecycle ---------------------------------------------------------

    def verify(self, identity: Identity, method: str = "automated") -> Identity:
        result = self._lifecycle.verify(identity, method)
        self._update_identity(result)
        self._emit_event("identity.updated", result)
        return result

    def supersede(self, identity: Identity, replacement_id: str) -> Identity:
        result = self._lifecycle.supersede(identity, replacement_id)
        self._update_identity(result)
        self._emit_event("identity.updated", result)
        return result

    def merge(self, primary_id: str, secondary_id: str, tenant_id: int) -> bool:
        result = self._resolver.merge(primary_id, secondary_id, tenant_id)
        if result:
            self._emit_event("identity.merged", Identity(identity_id=primary_id, tenant_id=tenant_id))
        return result

    def archive(self, identity: Identity, reason: str = "Archived") -> Identity:
        result = self._lifecycle.archive(identity, reason)
        self._update_identity(result)
        self._emit_event("identity.archived", result)
        return result

    # ---- Health ------------------------------------------------------------

    def _health_check(self) -> Any:
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus
        return HealthCheckResult(
            component="identity_engine",
            status=HealthStatus.HEALTHY,
            detail="Identity Engine operational",
            metrics={"resolver": type(self._resolver).__name__},
        )

    # ---- Events ------------------------------------------------------------

    def _emit_event(self, event_type: str, identity: Identity) -> None:
        if self._event_bus is None:
            return
        from app.shunya.infrastructure.event_bus import CanonicalEvent
        event = CanonicalEvent(
            event_type=event_type,
            actor_name="identity_engine",
            object_id=identity.identity_id,
            object_type="identity",
            object_version=1,
            payload={
                "identity_id": identity.identity_id,
                "person_id": identity.person_id,
                "identity_type": identity.identity_type,
                "tenant_id": identity.tenant_id,
                "status": identity.status,
            },
        )
        self._event_bus.publish(event)

    # ---- Internal ----------------------------------------------------------

    def _update_identity(self, identity: Identity) -> None:
        """Persist updated identity to Knowledge Store."""
        # Find KnowledgeObject by key lookup
        namespace = f"identity:{identity.tenant_id}"
        key = f"identity:{identity.identity_type}:{identity.normalized_value}"
        obj = self._ks.get_by_key(namespace, key)
        if obj:
            try:
                self._ks.update(obj.object_id, payload=identity.to_dict())
            except Exception:
                pass

    def _record_metrics(self, operation: str, start: float, result: ResolutionResult) -> None:
        duration = (time.time() - start) * 1000
        if self._metrics:
            self._resolve_counter.inc()
            if result.status == ResolutionStatus.MATCHED:
                self._match_counter.inc()
            elif result.status == ResolutionStatus.AMBIGUOUS:
                self._ambig_counter.inc()

    @property
    def resolver(self) -> IdentityResolver:
        return self._resolver


# ---- Module-level convenience -----------------------------------------------

_engine: Optional[IdentityEngine] = None


def get_identity_engine(**kwargs: Any) -> IdentityEngine:
    global _engine
    if _engine is None:
        from app.shunya.knowledge_store.store import get_knowledge_store
        _engine = IdentityEngine(knowledge_store=get_knowledge_store(), **kwargs)
    return _engine


def reset_identity_engine() -> None:
    global _engine
    _engine = None