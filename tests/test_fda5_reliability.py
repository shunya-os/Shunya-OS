"""FDA5-G6: Reliability Fabric tests."""
import time
import pytest


class TestReliabilityFabric:
    """Retry, circuit breaker, idempotency, failure classification."""

    def test_retry_policy_defaults(self):
        from core.reliability_fabric import RetryPolicy
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.base_delay == 1.0
        assert p.max_delay == 60.0
        assert p.backoff_factor == 2.0
        assert p.jitter is True

    def test_retry_policy_delay_calculation(self):
        from core.reliability_fabric import RetryPolicy
        p = RetryPolicy(base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert p.get_delay(1) == 1.0
        assert p.get_delay(2) == 2.0
        assert p.get_delay(3) == 4.0

    def test_retry_policy_delay_capped(self):
        from core.reliability_fabric import RetryPolicy
        p = RetryPolicy(base_delay=10.0, max_delay=15.0, jitter=False)
        assert p.get_delay(1) == 10.0
        assert p.get_delay(2) == 15.0  # capped

    def test_retry_should_retry(self):
        from core.reliability_fabric import RetryPolicy, FailureType
        p = RetryPolicy(max_retries=3)
        assert p.should_retry(1, FailureType.TRANSIENT)
        assert p.should_retry(2, FailureType.RATE_LIMITED)
        assert not p.should_retry(3, FailureType.TRANSIENT)  # max retries
        assert not p.should_retry(1, FailureType.PERMANENT)
        assert not p.should_retry(1, FailureType.VALIDATION)

    def test_failure_classification(self):
        from core.reliability_fabric import FailureType, _classify_failure
        assert _classify_failure(TimeoutError("timed out")) == FailureType.TIMEOUT
        assert _classify_failure(Exception("rate limit: too many")) == FailureType.RATE_LIMITED
        assert _classify_failure(Exception("auth token expired")) == FailureType.AUTH_EXPIRED
        assert _classify_failure(Exception("already exists: dup")) == FailureType.DUPLICATE
        assert _classify_failure(Exception("invalid request")) == FailureType.VALIDATION
        assert _classify_failure(Exception("connection refused")) == FailureType.PROVIDER_OUTAGE
        assert _classify_failure(Exception("unknown error")) == FailureType.TRANSIENT

    def test_with_retry_success(self):
        from core.reliability_fabric import with_retry, RetryPolicy
        call_count = 0

        @with_retry(policy=RetryPolicy(max_retries=3))
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_with_retry_eventual_success(self):
        from core.reliability_fabric import with_retry, RetryPolicy
        call_count = 0

        @with_retry(policy=RetryPolicy(max_retries=3, jitter=False))
        def eventually_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timed out")
            return "recovered"

        result = eventually_succeed()
        assert result == "recovered"
        assert call_count == 3

    def test_with_retry_permanent_failure(self):
        from core.reliability_fabric import with_retry, RetryPolicy
        call_count = 0

        @with_retry(policy=RetryPolicy(max_retries=3))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            always_fail()
        assert call_count == 3

    def test_circuit_breaker_initial_state(self):
        from core.reliability_fabric import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_opens_on_failures(self):
        from core.reliability_fabric import CircuitBreaker, CircuitState
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=60)
        assert cb.state == CircuitState.CLOSED

        # Simulate failures
        def fail():
            raise ConnectionError("provider down")

        for i in range(2):
            try:
                cb.call(fail)
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_blocks_when_open(self):
        from core.reliability_fabric import (
            CircuitBreaker, CircuitState, CircuitBreakerOpenError,
        )
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=60)

        def fail():
            raise ConnectionError("down")

        try:
            cb.call(fail)
        except ConnectionError:
            pass

        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "ok")

    def test_circuit_breaker_half_open_recovery(self):
        from core.reliability_fabric import (
            CircuitBreaker, CircuitState,
        )
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.05)

        def fail():
            raise ConnectionError("down")

        # Open the circuit
        try:
            cb.call(fail)
        except ConnectionError:
            pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.06)

        # Should transition to HALF_OPEN
        assert cb.get_state() == CircuitState.HALF_OPEN

        # Successful call closes the circuit
        cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED

    def test_idempotency_registry(self):
        from core.reliability_fabric import IdempotencyRegistry
        reg = IdempotencyRegistry()

        # First use: proceed
        assert reg.check_and_set("op_1") is True

        # Duplicate within TTL: reject
        assert reg.check_and_set("op_1") is False

        # Different key: proceed
        assert reg.check_and_set("op_2") is True

    def test_idempotency_store_and_retrieve(self):
        from core.reliability_fabric import IdempotencyRegistry
        reg = IdempotencyRegistry()

        key = "store_test"
        reg.check_and_set(key)
        reg.store_result(key, {"status": "done"})

        # Duplicate gets the stored result
        assert reg.check_and_set(key) is False
        assert reg.get_result(key) == {"status": "done"}

    def test_idempotency_cleanup(self):
        from core.reliability_fabric import IdempotencyRegistry
        reg = IdempotencyRegistry()

        reg.check_and_set("old_key")
        # Force cleanup by using very short TTL
        cleaned = reg.cleanup_expired(ttl_seconds=0)
        assert cleaned >= 1