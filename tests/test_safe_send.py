from app.communication.registry import get_provider
from app.communication.safe_send import safe_send


def test_safe_send(app):
    with app.app_context():
        provider = get_provider()

        result = safe_send(provider, "9999999999", "hello")

        assert result["status"] in ["sent", "blocked", "skipped"]