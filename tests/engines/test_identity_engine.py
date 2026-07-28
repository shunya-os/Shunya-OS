"""Tests for Phase D — Identity Engine Foundation."""

import threading
import pytest
from typing import Optional
from app.shunya.identity.models import (
    Identity, IdentityClaim, ResolutionResult, ResolutionStatus,
    IdentityStatus, IdentityType,
)
from app.shunya.identity.engine import IdentityEngine, get_identity_engine, reset_identity_engine
from app.shunya.identity.resolver import IdentityResolver
from app.shunya.identity.lifecycle import LifecycleEngine, InvalidTransitionError
from app.shunya.identity.normalizer import (
    normalize_email, normalize_phone, normalize_name, normalize_for_type, identity_type_strength,
)
from app.shunya.knowledge_store.store import KnowledgeStore


def _make_store() -> KnowledgeStore:
    return KnowledgeStore()


def _make_engine(ks: Optional[KnowledgeStore] = None, bus=None) -> IdentityEngine:
    store = ks or _make_store()
    return IdentityEngine(knowledge_store=store, event_bus=bus)


# ---------------------------------------------------------------------------
# Normalizer tests
# ---------------------------------------------------------------------------

class TestNormalizer:
    def test_normalize_email(self) -> None:
        assert normalize_email("User@Example.COM") == "user@example.com"
        assert normalize_email("") == ""

    def test_normalize_phone(self) -> None:
        assert normalize_phone("+1 (555) 123-4567") == "+15551234567"
        assert normalize_phone("919999999999") == "919999999999"
        assert normalize_phone("") == ""

    def test_normalize_name(self) -> None:
        assert normalize_name("  john  DOE ") == "John Doe"
        assert normalize_name("") == ""

    def test_normalize_for_type(self) -> None:
        assert normalize_for_type("email", "A@B.COM") == "a@b.com"
        assert normalize_for_type("phone", "+1-555-1234") == "+15551234"
        assert normalize_for_type("channel:whatsapp", "  +919999  ") == "+919999"

    def test_identity_type_strength(self) -> None:
        assert identity_type_strength("email") == "strong"
        assert identity_type_strength("phone") == "strong"
        assert identity_type_strength("external_id") == "medium"
        assert identity_type_strength("alias") == "weak"


# ---------------------------------------------------------------------------
# Identity model tests
# ---------------------------------------------------------------------------

class TestIdentity:
    def test_default_fields(self) -> None:
        identity = Identity(identity_type="email", identity_value="a@b.com")
        assert identity.identity_id
        assert identity.status == IdentityStatus.ACTIVE.value
        assert identity.tenant_id == 0
        assert identity.created_at is not None
        assert identity.updated_at is not None
        assert identity.verification_state == "unverified"

    def test_to_dict_roundtrip(self) -> None:
        i = Identity(identity_type="email", identity_value="a@b.com",
                      normalized_value="a@b.com", tenant_id=1, person_id="p1")
        d = i.to_dict()
        restored = Identity.from_dict(d)
        assert restored.identity_id == i.identity_id
        assert restored.person_id == i.person_id
        assert restored.identity_value == i.identity_value
        assert restored.tenant_id == i.tenant_id

    def test_is_active(self) -> None:
        active = Identity(identity_type="email", identity_value="a@b.com")
        assert active.is_active
        archived = Identity(identity_type="email", identity_value="a@b.com",
                            status=IdentityStatus.ARCHIVED.value)
        assert not archived.is_active

    def test_is_verified(self) -> None:
        unverified = Identity(identity_type="email", identity_value="a@b.com")
        assert not unverified.is_verified
        verified = Identity(identity_type="email", identity_value="a@b.com",
                            verification_state="verified")
        assert verified.is_verified


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------

class TestLifecycleEngine:
    def test_verify(self) -> None:
        lc = LifecycleEngine()
        identity = Identity(identity_type="email", identity_value="a@b.com")
        result = lc.verify(identity)
        assert result.status == IdentityStatus.VERIFIED.value

    def test_supersede(self) -> None:
        lc = LifecycleEngine()
        identity = Identity(identity_type="email", identity_value="a@b.com")
        result = lc.supersede(identity, "new-id")
        assert result.status == IdentityStatus.SUPERSEDED.value
        assert result.superseded_at is not None
        assert result.metadata.get("superseded_by") == "new-id"

    def test_merge(self) -> None:
        lc = LifecycleEngine()
        identity = Identity(identity_type="email", identity_value="a@b.com")
        result = lc.merge(identity, "primary-id")
        assert result.status == IdentityStatus.MERGED.value
        assert result.merged_into_id == "primary-id"

    def test_archive(self) -> None:
        lc = LifecycleEngine()
        identity = Identity(identity_type="email", identity_value="a@b.com")
        result = lc.archive(identity)
        assert result.status == IdentityStatus.ARCHIVED.value

    def test_invalid_transition_from_terminal(self) -> None:
        lc = LifecycleEngine()
        identity = Identity(identity_type="email", identity_value="a@b.com")
        lc.archive(identity)
        with pytest.raises(InvalidTransitionError):
            lc.verify(identity)

    def test_invalid_transition(self) -> None:
        lc = LifecycleEngine()
        identity = Identity(identity_type="email", identity_value="a@b.com")
        with pytest.raises(InvalidTransitionError):
            lc.transition(identity, "nonexistent")

    def test_can_transition(self) -> None:
        lc = LifecycleEngine()
        assert lc.can_transition(IdentityStatus.ACTIVE.value, IdentityStatus.VERIFIED.value)
        assert not lc.can_transition(IdentityStatus.ARCHIVED.value, IdentityStatus.ACTIVE.value)

    def test_is_terminal(self) -> None:
        lc = LifecycleEngine()
        assert lc.is_terminal(IdentityStatus.SUPERSEDED.value)
        assert not lc.is_terminal(IdentityStatus.ACTIVE.value)


# ---------------------------------------------------------------------------
# IdentityResolver tests
# ---------------------------------------------------------------------------

class TestIdentityResolver:
    def test_resolve_by_email(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        resolver.register_with_person("email", "a@b.com", 1, "p1")
        result = resolver.resolve_by_email("a@b.com", 1)
        assert result.status == ResolutionStatus.MATCHED

    def test_resolve_no_match(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        result = resolver.resolve_by_email("nonexistent@example.com", 1)
        assert result.status == ResolutionStatus.NO_MATCH

    def test_resolve_by_phone(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        resolver.register_with_person("phone", "+1-555-1234", 1, "p1")
        result = resolver.resolve_by_phone("+1-555-1234", 1)
        assert result.status == ResolutionStatus.MATCHED

    def test_resolve_by_channel(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        resolver.register_with_person("channel:whatsapp", "+919999", 1, "p1")
        result = resolver.resolve_by_channel("whatsapp", "+919999", 1)
        assert result.status == ResolutionStatus.MATCHED

    def test_resolve_multi_email_first(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        resolver.register_with_person("email", "a@b.com", 1, "p1")
        result = resolver.resolve_multi(email="a@b.com", phone="+1555123", tenant_id=1)
        assert result.status == ResolutionStatus.MATCHED

    def test_resolve_tenant_isolation(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        resolver.register_with_person("email", "shared@domain.com", 1, "p1")
        result = resolver.resolve_by_email("shared@domain.com", 2)
        assert result.status == ResolutionStatus.NO_MATCH

    def test_register_existing_returns_none(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        resolver.register_with_person("email", "a@b.com", 1, "p1")
        result = resolver.register("email", "a@b.com", 1)
        assert result is None  # duplicate

    def test_merge(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        p1 = resolver.register_with_person("email", "a@b.com", 1, "p1")
        p2 = resolver.register_with_person("email", "c@d.com", 1, "p2")
        assert resolver.merge(p1.identity_id, p2.identity_id, 1) is True

    def test_merge_nonexistent(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        assert resolver.merge("nonexistent", "also-nonexistent", 1) is False

    def test_register_with_person(self) -> None:
        ks = _make_store()
        resolver = IdentityResolver(ks)
        result = resolver.register_with_person("email", "new@example.com", 1, "person-42")
        assert result is not None
        assert result.person_id == "person-42"


# ---------------------------------------------------------------------------
# IdentityEngine tests
# ---------------------------------------------------------------------------

class TestIdentityEngine:
    def test_resolve(self) -> None:
        engine = _make_engine()
        engine.register("email", "user@example.com", 1, person_id="p1")
        result = engine.resolve(IdentityClaim(identity_type="email", identity_value="user@example.com", tenant_id=1))
        assert result.status == ResolutionStatus.MATCHED
        assert result.identity is not None

    def test_resolve_no_match(self) -> None:
        engine = _make_engine()
        result = engine.resolve(IdentityClaim(identity_type="email", identity_value="no@one.com", tenant_id=1))
        assert result.status == ResolutionStatus.NO_MATCH

    def test_register_duplicate(self) -> None:
        engine = _make_engine()
        engine.register("email", "dup@example.com", 1, person_id="p1")
        result = engine.register("email", "dup@example.com", 1, person_id="p2")
        assert result is None

    def test_verify(self) -> None:
        engine = _make_engine()
        identity = engine.register("email", "a@b.com", 1, person_id="p1")
        verified = engine.verify(identity)
        assert verified.status == IdentityStatus.VERIFIED.value

    def test_archive(self) -> None:
        engine = _make_engine()
        identity = engine.register("email", "a@b.com", 1, person_id="p1")
        archived = engine.archive(identity)
        assert archived.status == IdentityStatus.ARCHIVED.value

    def test_merge(self) -> None:
        engine = _make_engine()
        p1 = engine.register("email", "a@b.com", 1, person_id="p1")
        p2 = engine.register("email", "c@d.com", 1, person_id="p2")
        assert engine.merge(p1.identity_id, p2.identity_id, 1) is True

    def test_resolve_multi(self) -> None:
        engine = _make_engine()
        engine.register("email", "primary@example.com", 1, person_id="p1")
        result = engine.resolve_multi(email="primary@example.com", tenant_id=1)
        assert result.status == ResolutionStatus.MATCHED

    def test_convenience_methods(self) -> None:
        engine = _make_engine()
        engine.register("email", "test@test.com", 1, person_id="p1")
        r1 = engine.resolve_by_email("test@test.com", 1)
        assert r1.status == ResolutionStatus.MATCHED
        r2 = engine.resolve_by_phone("+1555123", 1)
        assert r2.status == ResolutionStatus.NO_MATCH
        r3 = engine.resolve_by_channel("telegram", "12345", 1)
        assert r3.status == ResolutionStatus.NO_MATCH

    def test_health_check(self) -> None:
        from app.shunya.infrastructure.health import HealthRegistry
        health = HealthRegistry()
        engine = IdentityEngine(knowledge_store=_make_store(), health_registry=health)
        check = health.check_all()
        identity_check = [c for c in check if c.component == "identity_engine"]
        assert len(identity_check) == 1
        assert identity_check[0].status.value == "healthy"

    def test_supersede(self) -> None:
        engine = _make_engine()
        identity = engine.register("email", "old@test.com", 1, person_id="p1")
        result = engine.supersede(identity, "new-id")
        assert result.status == IdentityStatus.SUPERSEDED.value
        assert result.metadata.get("superseded_by") == "new-id"

    def test_register_with_person(self) -> None:
        engine = _make_engine()
        identity = engine.register_with_person("email", "person@test.com", 1, person_id="p42")
        assert identity is not None
        assert identity.person_id == "p42"
        result = engine.resolve_by_email("person@test.com", 1)
        assert result.status == ResolutionStatus.MATCHED

    def test_resolve_empty_claim(self) -> None:
        engine = _make_engine()
        result = engine.resolve(IdentityClaim(identity_type="email", identity_value="", tenant_id=1))
        assert result.status == ResolutionStatus.NO_MATCH

    def test_engine_with_metrics(self) -> None:
        from app.shunya.infrastructure.metrics import MetricsRegistry
        from app.shunya.infrastructure.event_bus import EventBus
        metrics = MetricsRegistry()
        bus = EventBus()
        engine = IdentityEngine(
            knowledge_store=_make_store(),
            metrics_registry=metrics,
            event_bus=bus,
        )
        engine.register("email", "metrics@test.com", 1, person_id="p1")
        engine.resolve(IdentityClaim(identity_type="email", identity_value="metrics@test.com", tenant_id=1))
        engine.resolve(IdentityClaim(identity_type="email", identity_value="unknown@test.com", tenant_id=1))
        exposition = metrics.generate_exposition()
        assert "identity_resolutions_total" in exposition
        assert "identity_matches_total" in exposition


# ---------------------------------------------------------------------------
# Concurrency tests
# ---------------------------------------------------------------------------

class TestIdentityConcurrency:
    def test_concurrent_resolve(self) -> None:
        engine = _make_engine()
        engine.register("email", "shared@test.com", 1, person_id="p1")
        errors = []
        def resolve() -> None:
            try:
                result = engine.resolve(IdentityClaim(identity_type="email", identity_value="shared@test.com", tenant_id=1))
                assert result.status == ResolutionStatus.MATCHED
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=resolve) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0

    def test_concurrent_register_different(self) -> None:
        engine = _make_engine()
        errors = []
        def register(n: int) -> None:
            try:
                engine.register("email", f"user{n}@test.com", 1, person_id=f"p{n}")
            except Exception as e:
                errors.append(e)
        threads = [threading.Thread(target=register, args=(i,)) for i in range(20)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0


# ---------------------------------------------------------------------------
# Event integration tests
# ---------------------------------------------------------------------------

class TestIdentityEvents:
    def test_register_emits_event(self) -> None:
        from app.shunya.infrastructure.event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("identity.*", lambda e: received.append(e), "evt")
        engine = _make_engine(bus=bus)
        engine.register("email", "event@test.com", 1, person_id="p1")
        assert any(e.event_type == "identity.created" for e in received)

    def test_archive_emits_event(self) -> None:
        from app.shunya.infrastructure.event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("identity.*", lambda e: received.append(e), "evt")
        engine = _make_engine(bus=bus)
        identity = engine.register("email", "arch@test.com", 1, person_id="p1")
        engine.archive(identity)
        assert any(e.event_type == "identity.archived" for e in received)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

class TestIdentityModule:
    def test_get_singleton(self) -> None:
        reset_identity_engine()
        e1 = get_identity_engine()
        e2 = get_identity_engine()
        assert e1 is e2

    def test_reset(self) -> None:
        e1 = get_identity_engine()
        reset_identity_engine()
        e2 = get_identity_engine()
        assert e1 is not e2