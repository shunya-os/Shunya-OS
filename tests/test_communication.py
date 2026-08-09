from app.communication.registry import get_provider

def test_provider_send():
    provider = get_provider()
    result = provider.send("9999999999", "hello")

    assert result["status"] == "sent"
    assert result["provider"] == "openwa"