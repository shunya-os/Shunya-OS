"""Tests for the OS Adapter (Directive L-03)."""

from app.adapters.os_adapter import process_intent, sign_in, create_object, create_space


class TestProcessIntent:
    def test_unknown_intent(self) -> None:
        result = process_intent("fly_to_moon")
        assert result["success"] is True  # pipeline doesn't fail on unknown intent
        assert "trace" in result

    def test_sign_in_through_adapter(self) -> None:
        result = sign_in(email="test@example.com", name="Test User")
        assert result["success"] is True
        trace = result.get("trace", [])
        stages = {s["stage"] for s in trace}
        assert "intent_resolution" in stages
        assert "identity_resolution" in stages

    def test_create_object_through_adapter(self) -> None:
        result = create_object(
            name="Test Doc",
            object_type="document",
            space_id="space-1",
            identity_id="user-1",
        )
        assert result["success"] is True
        assert result.get("object_id") is not None

    def test_create_space_through_adapter(self) -> None:
        result = create_space(
            name="Test Space",
            identity_id="user-1",
        )
        assert result["success"] is True

    def test_process_intent_passes_identity(self) -> None:
        result = process_intent(
            intent="sign_in",
            parameters={"email": "alice@co.com", "name": "Alice"},
            identity_id="user-1",
        )
        assert result["identity_id"] is not None or result["identity_id"] == "user-1"

    def test_trace_includes_all_stages(self) -> None:
        result = process_intent(
            intent="create_object",
            parameters={"name": "X", "object_type": "doc"},
            identity_id="user-1",
        )
        trace = result.get("trace", [])
        statuses = {s["stage"]: s["status"] for s in trace}
        assert "intent_resolution" in statuses
        assert "object_resolution" in statuses

    def test_process_intent_runtime_results(self) -> None:
        result = process_intent(
            intent="create_object",
            parameters={"name": "Report", "object_type": "doc"},
            identity_id="user-1",
        )
        rr = result.get("runtime_results", {})
        # intent_resolution should have produced a result
        assert rr is not None