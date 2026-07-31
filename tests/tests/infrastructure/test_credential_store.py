"""Tests for INFR-008: Credential Store (ADR-003)."""

import os
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional
import pytest
from app.shunya.infrastructure.credential_store import (
    CredentialStore, CredentialRef, ResolvedCredential,
    LocalCredentialProvider, EnvVarCredentialProvider,
    AccessPolicy, AuditLog, EligibilityGate,
    AccessDeniedError, CredentialNotFoundError,
    EligibilityDeniedError, CredentialExpiredError,
    encrypt_value, decrypt_value,
    get_credential_store, reset_credential_store,
    CredentialType, CredentialMetadata,
)


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self) -> None:
        original = "my-secret-api-token"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_different_ciphertexts(self) -> None:
        value = "same-value"
        e1 = encrypt_value(value)
        e2 = encrypt_value(value)
        assert e1 != e2  # Different salts

    def test_decrypt_wrong_key_fails(self) -> None:
        value = "secret"
        encrypted = encrypt_value(value, key=b"a" * 32)
        import hashlib
        wrong_key = hashlib.sha256(b"wrong-key").digest()
        with pytest.raises(Exception):
            decrypt_value(encrypted, key=wrong_key)


class TestLocalCredentialProvider:
    def test_store_and_resolve(self) -> None:
        provider = LocalCredentialProvider()
        ref = CredentialRef(alias="my_token", tenant_id=1)
        provider.store(ref, "secret-value", "api_token")
        resolved = provider.resolve(ref)
        assert resolved.value == "secret-value"
        assert resolved.type == "api_token"

    def test_resolve_not_found(self) -> None:
        provider = LocalCredentialProvider()
        ref = CredentialRef(alias="nonexistent", tenant_id=1)
        with pytest.raises(CredentialNotFoundError):
            provider.resolve(ref)

    def test_tenant_isolation(self) -> None:
        provider = LocalCredentialProvider()
        provider.store(CredentialRef(alias="key", tenant_id=1), "secret-1", "api_token")
        with pytest.raises(CredentialNotFoundError):
            provider.resolve(CredentialRef(alias="key", tenant_id=2))

    def test_revoke(self) -> None:
        provider = LocalCredentialProvider()
        ref = CredentialRef(alias="my_key", tenant_id=1)
        meta = provider.store(ref, "secret", "api_token")
        assert provider.revoke(meta.credential_id, 1, "test") is True
        with pytest.raises(CredentialExpiredError):
            provider.resolve(ref)

    def test_list(self) -> None:
        provider = LocalCredentialProvider()
        provider.store(CredentialRef(alias="k1", tenant_id=1), "v1", "api_token")
        provider.store(CredentialRef(alias="k2", tenant_id=1), "v2", "password")
        provider.store(CredentialRef(alias="k3", tenant_id=2), "v3", "api_token")
        items = provider.list(tenant_id=1)
        assert len(items) == 2
        items = provider.list(tenant_id=1, credential_type="password")
        assert len(items) == 1

    def test_clear(self) -> None:
        provider = LocalCredentialProvider()
        provider.store(CredentialRef(alias="k", tenant_id=1), "v", "api_token")
        provider.clear()
        assert len(provider.list(tenant_id=1)) == 0

    def test_expiry(self) -> None:
        provider = LocalCredentialProvider()
        ref = CredentialRef(alias="temp", tenant_id=1)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        provider.store(ref, "temp-value", "api_token", metadata={"expires_at": past})
        with pytest.raises(CredentialExpiredError):
            provider.resolve(ref)


class TestEnvVarCredentialProvider:
    def test_resolve_from_env(self) -> None:
        os.environ["SHUNYA_CREDENTIAL_MY_KEY"] = "env-value"
        try:
            provider = EnvVarCredentialProvider()
            ref = CredentialRef(alias="my_key", tenant_id=1)
            resolved = provider.resolve(ref)
            assert resolved.value == "env-value"
        finally:
            del os.environ["SHUNYA_CREDENTIAL_MY_KEY"]

    def test_resolve_not_found(self) -> None:
        provider = EnvVarCredentialProvider()
        with pytest.raises(CredentialNotFoundError):
            provider.resolve(CredentialRef(alias="nonexistent", tenant_id=1))

    def test_list(self) -> None:
        os.environ["SHUNYA_CREDENTIAL_A"] = "val-a"
        os.environ["SHUNYA_CREDENTIAL_B"] = "val-b"
        try:
            provider = EnvVarCredentialProvider()
            items = provider.list(tenant_id=1)
            aliases = [i.alias for i in items]
            assert "a" in aliases
            assert "b" in aliases
        finally:
            del os.environ["SHUNYA_CREDENTIAL_A"]
            del os.environ["SHUNYA_CREDENTIAL_B"]

    def test_store_raises(self) -> None:
        provider = EnvVarCredentialProvider()
        with pytest.raises(NotImplementedError):
            provider.store(CredentialRef(alias="x", tenant_id=1), "v", "api_token")


class TestAccessPolicy:
    def test_authorize_default(self) -> None:
        policy = AccessPolicy()
        policy.authorize("executor_engine")  # Should not raise

    def test_authorize_denied(self) -> None:
        policy = AccessPolicy()
        with pytest.raises(AccessDeniedError):
            policy.authorize("unknown_engine")

    def test_add_caller(self) -> None:
        policy = AccessPolicy()
        policy.add_caller("test_engine")
        policy.authorize("test_engine")  # Should not raise

    def test_remove_caller(self) -> None:
        policy = AccessPolicy()
        policy.remove_caller("executor_engine")
        with pytest.raises(AccessDeniedError):
            policy.authorize("executor_engine")


class TestCredentialStore:
    def test_resolve_success(self) -> None:
        store = CredentialStore()
        ref = CredentialRef(alias="test_key", tenant_id=1)
        store.store(ref, "my-secret", "api_token")
        resolved = store.resolve(ref, caller_name="executor_engine")
        assert resolved.value == "my-secret"

    def test_resolve_access_denied(self) -> None:
        store = CredentialStore()
        ref = CredentialRef(alias="test_key", tenant_id=1)
        store.store(ref, "secret", "api_token")
        with pytest.raises(AccessDeniedError):
            store.resolve(ref, caller_name="unknown_engine")

    def test_resolve_eligibility_denied(self) -> None:
        gate = EligibilityGate(gate_fn=lambda pc, ct: False)
        store = CredentialStore(eligibility_gate=gate)
        ref = CredentialRef(alias="test_key", tenant_id=1)
        store.store(ref, "secret", "api_token")
        with pytest.raises(EligibilityDeniedError):
            store.resolve(ref, caller_name="executor_engine")

    def test_resolve_not_found(self) -> None:
        store = CredentialStore()
        ref = CredentialRef(alias="nonexistent", tenant_id=1)
        with pytest.raises(CredentialNotFoundError):
            store.resolve(ref, caller_name="executor_engine")

    def test_store_and_list(self) -> None:
        store = CredentialStore()
        store.store(CredentialRef(alias="k1", tenant_id=1), "v1", "api_token")
        store.store(CredentialRef(alias="k2", tenant_id=1), "v2", "password")
        items = store.list(tenant_id=1)
        assert len(items) == 2

    def test_revoke(self) -> None:
        store = CredentialStore()
        ref = CredentialRef(alias="revokable", tenant_id=1)
        meta = store.store(ref, "secret", "api_token")
        assert store.revoke(meta.credential_id, 1, "test") is True
        with pytest.raises(CredentialExpiredError):
            store.resolve(ref, caller_name="executor_engine")

    def test_rotate(self) -> None:
        store = CredentialStore()
        ref = CredentialRef(alias="rotatable", tenant_id=1)
        meta = store.store(ref, "old-secret", "api_token")
        assert store.rotate(meta.credential_id, 1, "new-secret") is True
        # Old credential_id is deleted when new credential is stored under same alias
        old_ref = CredentialRef(credential_id=meta.credential_id, tenant_id=1)
        with pytest.raises(CredentialNotFoundError):
            store.resolve(old_ref, caller_name="executor_engine")
        # New value accessible via alias
        resolved = store.resolve(ref, caller_name="executor_engine")
        assert resolved.value == "new-secret"

    def test_tenant_isolation(self) -> None:
        store = CredentialStore()
        store.store(CredentialRef(alias="key", tenant_id=1), "secret-1", "api_token")
        with pytest.raises(CredentialNotFoundError):
            store.resolve(CredentialRef(alias="key", tenant_id=2), caller_name="executor_engine")


class TestCredentialStoreHealth:
    def test_health_check(self) -> None:
        store = CredentialStore()
        check = store._health_check()
        assert check.status.value == "healthy"
        assert "provider" in check.metrics


class TestCredentialStoreConcurrency:
    def test_concurrent_resolve(self) -> None:
        store = CredentialStore()
        ref = CredentialRef(alias="concurrent", tenant_id=1)
        store.store(ref, "shared-secret", "api_token")
        errors = []

        def resolve_thread() -> None:
            try:
                r = store.resolve(ref, caller_name="executor_engine")
                assert r.value == "shared-secret"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=resolve_thread) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_store(self) -> None:
        store = CredentialStore()
        errors = []

        def store_thread(n: int) -> None:
            try:
                store.store(CredentialRef(alias=f"key{n}", tenant_id=1), f"val{n}", "api_token")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=store_thread, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(store.list(tenant_id=1)) == 20


class TestCredentialStoreModuleLevel:
    def test_get_credential_store_singleton(self) -> None:
        reset_credential_store()
        s1 = get_credential_store()
        s2 = get_credential_store()
        assert s1 is s2

    def test_reset_credential_store(self) -> None:
        s1 = get_credential_store()
        reset_credential_store()
        s2 = get_credential_store()
        assert s1 is not s2

    def test_store_update_existing(self) -> None:
        provider = LocalCredentialProvider()
        ref = CredentialRef(alias="update_me", tenant_id=1)
        meta1 = provider.store(ref, "v1", "api_token")
        meta2 = provider.store(ref, "v2", "api_token")
        assert meta2.version == 2
        resolved = provider.resolve(ref)
        assert resolved.value == "v2"

    def test_eligibility_gate_default_allows(self) -> None:
        gate = EligibilityGate()
        assert gate.check("any_purpose", "credential") is True

    def test_eligibility_gate_unavailable_denies(self) -> None:
        def failing(purpose_code, credential_type):
            raise RuntimeError("gate unavailable")
        gate = EligibilityGate(gate_fn=failing)
        assert gate.check("any", "credential") is False

    def test_access_policy_error_message(self) -> None:
        policy = AccessPolicy()
        try:
            policy.authorize("unknown")
        except AccessDeniedError as e:
            assert "executor_engine" in str(e)

    def test_audit_log_query(self) -> None:
        log = AuditLog()
        log.record("c1", "alias1", "resolve", "executor", 1, True)
        log.record("c2", "alias2", "store", "admin", 1, True)
        entries = log.query(operation="resolve")
        assert len(entries) == 1
        assert entries[0].credential_id == "c1"

    def test_store_resolve_different_credential_types(self) -> None:
        store = CredentialStore()
        store.store(CredentialRef(alias="api", tenant_id=1), "api-val", "api_token")
        store.store(CredentialRef(alias="pwd", tenant_id=1), "pwd-val", "password")
        r1 = store.resolve(CredentialRef(alias="api", tenant_id=1), caller_name="executor_engine")
        r2 = store.resolve(CredentialRef(alias="pwd", tenant_id=1), caller_name="executor_engine")
        assert r1.value == "api-val"
        assert r2.value == "pwd-val"