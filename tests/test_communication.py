from app.communication.registry import get_provider


def test_provider_send():
    provider = get_provider()
    # Must pass is_human_triggered=True to pass the guardrail
    result = provider.send("9999999999", "hello", metadata={"is_human_triggered": True})

    assert result["status"] == "sent"
    assert result["provider"] == "openwa"


def test_provider_send_blocked_without_human():
    """Direct send without is_human_triggered must be blocked."""
    import pytest
    provider = get_provider()
    with pytest.raises(PermissionError):
        provider.send("9999999999", "hello")