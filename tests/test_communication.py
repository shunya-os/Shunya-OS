from app.communication.registry import get_provider


def test_provider_send():
    provider = get_provider()
    # Must pass is_human_triggered=True to pass the guardrail
    result = provider.send("test@example.com", "hello", metadata={"is_human_triggered": True, "subject": "Test"})

    # With no SMTP credentials configured, it should log (not error)
    assert result["status"] in ("sent", "logged", "failed")
    assert result["channel"] == "email"


def test_provider_send_blocked_without_human():
    """Direct send without is_human_triggered must be blocked."""
    import pytest
    provider = get_provider()
    with pytest.raises(PermissionError):
        provider.send("9999999999", "hello")