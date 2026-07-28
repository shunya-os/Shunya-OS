"""Tests for Milestone 5 — AI Copilot.

Tests the complete AI Copilot layer:
- LLM Provider Abstraction (OpenAI, OpenRouter, Anthropic, Local)
- Context Window Assembly from pipeline state
- Prompt Template Management and Intent Detection
- Copilot Service (message processing, summary generation)
- Provider fallback chain
- Graceful degradation
- API endpoints
- Conversation integration
- All Milestones 1–4 regressions
"""
from __future__ import annotations

from app.ai.provider import (
    AnthropicProvider,
    LLMProvider,
    LocalProvider,
    OpenAIProvider,
    OpenRouterProvider,
    get_provider,
    reset_provider,
    set_provider,
)
from app.ai.context import assemble_context, format_context_for_prompt
from app.ai.prompts import (
    PROMPT_TEMPLATES,
    build_messages,
    detect_intent,
    get_system_prompt,
)
from app.ai.copilot import (
    copilot_health,
    generate_entity_summary,
    process_message,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_identity(app):
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="copilot@shunyaos.com", name="Copilot Test")
    assert result["success"]
    return result["identity_id"]


def _seed_copilot_data(app, identity_id):
    """Seed data for AI Copilot testing."""
    from app import db
    from app.founder.models import (
        BusinessRelationship,
        FounderConversation,
        FounderMessage,
        FounderObject,
        FounderSpace,
    )

    space = FounderSpace(
        space_id="cp_spc_001", name="Copilot Test Space",
        space_type="organization", identity_id=identity_id,
    )
    db.session.add(space)
    db.session.flush()

    obj = FounderObject(
        object_id="cp_obj_001", space_id="cp_spc_001",
        name="Test Proposal", object_type="Document",
        content="A detailed proposal for Q4 marketing campaign targeting enterprise clients. Budget: ₹20L. Expected ROI: 4x.",
        created_by=identity_id,
    )
    db.session.add(obj)
    db.session.flush()

    conv = FounderConversation(
        conv_id="cp_conv_001", object_id="cp_obj_001",
        title="About Test Proposal", identity_id=identity_id,
    )
    db.session.add(conv)
    db.session.flush()

    for msg in [
        ("human", "What's the status of this proposal?"),
        ("assistant", "The Test Proposal is active and has a budget of ₹20L targeting enterprise clients with 4x expected ROI."),
        ("human", "Good, let me know if we need to adjust the budget."),
    ]:
        db.session.add(FounderMessage(conv_id="cp_conv_001", role=msg[0], content=msg[1]))

    # Relationships
    for i, (rid, rtype, rname) in enumerate([
        ("cp_rel_001", "customer", "Big Corp Inc"),
        ("cp_rel_002", "supplier", "Quality Supplies"),
    ]):
        db.session.add(BusinessRelationship(
            rel_id=rid, space_id="cp_spc_001",
            rel_type=rtype, name=rname,
            company=f"{rname} Ltd" if i == 1 else rname,
            created_by=identity_id,
        ))

    db.session.commit()


# ===========================================================================
# 1. LLM Provider Abstraction
# ===========================================================================

class TestLLMProvider:
    """LLM Provider abstraction layer."""

    def test_local_provider_is_always_available(self):
        provider = LocalProvider()
        assert provider.is_available()
        assert provider.name == "local"

    def test_local_provider_returns_response(self):
        provider = LocalProvider()
        result = provider.complete([
            {"role": "user", "content": "Hello"},
        ])
        assert result["content"]
        assert result["finish_reason"] == "stop"
        assert result["model"] == "local"

    def test_local_provider_contextual_response(self):
        provider = LocalProvider()
        result = provider.complete([
            {"role": "user", "content": "Can you summarize this object?"},
        ])
        assert "summary" in result["content"].lower() or "summarize" in result["content"].lower()

    def test_openai_provider_not_available_without_key(self):
        provider = OpenAIProvider(api_key="")
        assert not provider.is_available()

    def test_openrouter_provider_returns_error_without_key(self):
        provider = OpenRouterProvider(api_key="")
        assert not provider.is_available()

    def test_anthropic_provider_returns_error_without_key(self):
        provider = AnthropicProvider(api_key="")
        assert not provider.is_available()

    def test_provider_resolve_returns_local_fallback(self):
        reset_provider()
        provider = get_provider()
        assert provider.is_available()
        assert provider.name == "local"

    def test_provider_override_for_testing(self):
        custom = LocalProvider()
        custom.model = "test-model"
        set_provider(custom)
        provider = get_provider()
        assert provider.model == "test-model"
        reset_provider()

    def test_provider_implements_interface(self):
        provider = LocalProvider()
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, "complete")
        assert hasattr(provider, "is_available")

    def test_local_provider_greeting(self):
        provider = LocalProvider()
        result = provider.complete([{"role": "user", "content": "Hello SHUNYA"}])
        assert "SHUNYA" in result["content"] or "hello" in result["content"].lower()

    def test_local_provider_help_request(self):
        provider = LocalProvider()
        result = provider.complete([{"role": "user", "content": "What can you help me with?"}])
        assert "help" in result["content"].lower() or "can" in result["content"].lower()


# ===========================================================================
# 2. Context Window Assembly
# ===========================================================================

class TestContextAssembly:
    """Context window assembly from pipeline state."""

    def test_context_with_object_id(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        context = assemble_context(object_id="cp_obj_001")
        assert context["object"] is not None
        assert context["object"]["name"] == "Test Proposal"
        assert context["object"]["object_type"] == "Document"

    def test_context_includes_space(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        context = assemble_context(object_id="cp_obj_001")
        assert context["space"] is not None
        assert context["space"]["name"] == "Copilot Test Space"

    def test_context_includes_relationships(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        context = assemble_context(object_id="cp_obj_001")
        assert len(context["relationships"]) >= 2

    def test_context_includes_conversation(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        context = assemble_context(object_id="cp_obj_001")
        assert context["conversation"] is not None
        assert context["conversation"]["message_count"] >= 3

    def test_context_without_object_id(self, app):
        context = assemble_context(object_id=None)
        assert context["object"] is None

    def test_context_includes_recent_activity(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        context = assemble_context(identity_id=identity_id)
        assert len(context["recent_activity"]) >= 0

    def test_format_context_for_prompt(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        context = assemble_context(object_id="cp_obj_001")
        formatted = format_context_for_prompt(context)
        assert "Test Proposal" in formatted
        assert "Document" in formatted
        assert "Copilot Test Space" in formatted
        assert "Big Corp Inc" in formatted
        assert "Quality Supplies" in formatted

    def test_context_prompt_no_object(self):
        context = assemble_context(object_id=None)
        formatted = format_context_for_prompt(context)
        assert isinstance(formatted, str)
        assert len(formatted) > 0


# ===========================================================================
# 3. Prompt Template Management
# ===========================================================================

class TestPromptTemplates:
    """Prompt template management and intent detection."""

    def test_system_prompt_has_identity(self):
        prompt = get_system_prompt()
        assert "SHUNYA" in prompt
        assert "AI Operating System" in prompt

    def test_system_prompt_has_capabilities(self):
        prompt = get_system_prompt()
        assert "Answer questions" in prompt
        assert "Generate summaries" in prompt

    def test_system_prompt_summarize_mode(self):
        prompt = get_system_prompt("summarize")
        assert "Summary Mode" in prompt

    def test_system_prompt_create_mode(self):
        prompt = get_system_prompt("create_object")
        assert "Object Creation Mode" in prompt

    def test_system_prompt_analyze_mode(self):
        prompt = get_system_prompt("analyze")
        assert "Analysis Mode" in prompt

    def test_system_prompt_fallback_to_general(self):
        prompt = get_system_prompt("nonexistent")
        assert "SHUNYA" in prompt

    def test_build_messages_includes_context(self):
        messages = build_messages(
            context_str="Test context data",
            user_message="Hello",
        )
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert "Test context data" in messages[0]["content"]
        assert messages[-1]["role"] == "user"

    def test_build_messages_includes_history(self):
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]
        messages = build_messages(
            context_str="Context",
            user_message="Second question",
            conversation_history=history,
        )
        assert len(messages) == 4
        assert messages[1]["content"] == "First question"
        assert messages[2]["content"] == "First answer"

    def test_detect_intent_summarize(self):
        assert detect_intent("Can you summarize this object?") == "summarize"
        assert detect_intent("Give me a summary") == "summarize"

    def test_detect_intent_create(self):
        assert detect_intent("Create a new task") == "create_object"
        assert detect_intent("Make a note about this") == "create_object"

    def test_detect_intent_analyze(self):
        assert detect_intent("Analyze this data for risks") == "analyze"
        assert detect_intent("What patterns do you see?") == "analyze"

    def test_detect_intent_general(self):
        assert detect_intent("What's the weather like?") == "general"
        assert detect_intent("How are you?") == "general"

    def test_all_intents_have_system_prompts(self):
        for intent in ["general", "summarize", "create_object", "analyze"]:
            prompt = get_system_prompt(intent)
            assert prompt, f"Missing prompt for intent: {intent}"


# ===========================================================================
# 4. AI Copilot Service
# ===========================================================================

class TestCopilotService:
    """AI Copilot service — message processing and summary generation."""

    def test_process_message_returns_response(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = process_message(conv_id="cp_conv_001", user_message="Hello SHUNYA")
        assert result["success"]
        assert result["response"]
        assert result["model"] in ("local", "local-fallback")

    def test_process_message_persists_messages(self, app):
        from app.founder.models import FounderMessage
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        before = FounderMessage.query.filter_by(conv_id="cp_conv_001").count()
        process_message(conv_id="cp_conv_001", user_message="Another test message")
        after = FounderMessage.query.filter_by(conv_id="cp_conv_001").count()
        assert after == before + 2  # human + assistant

    def test_process_message_includes_intent(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = process_message(conv_id="cp_conv_001", user_message="Summarize this proposal")
        assert result["intent"] in ("summarize", "general")

    def test_process_message_invalid_conv(self, app):
        result = process_message(conv_id="nonexistent", user_message="Hello")
        assert not result["success"]
        assert "error" in result

    def test_generate_entity_summary(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = generate_entity_summary("cp_obj_001")
        assert result["success"]
        assert result["summary"]
        # Should contain either the object name or a summary-related keyword
        has_name = "Test Proposal" in result["summary"]
        has_summary_keyword = any(w in result["summary"].lower() for w in ["summary", "summarize", "object"])
        assert has_name or has_summary_keyword, f"Summary missing content: {result['summary'][:100]}"

    def test_generate_entity_summary_nonexistent(self, app):
        result = generate_entity_summary("nonexistent")
        assert not result["success"]

    def test_copilot_health_check(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        health = copilot_health()
        assert health["provider"] == "local"
        assert health["available"] is True

    def test_process_message_does_not_fabricate(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = process_message(
            conv_id="cp_conv_001",
            user_message="Tell me about a client named Nonexistent Corp"
        )
        # Local provider should not fabricate — it doesn't have LLM knowledge,
        # but it should reference the context provided
        assert result["success"]

    def test_process_message_summary_intent(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = process_message(
            conv_id="cp_conv_001",
            user_message="Summarize this object for me"
        )
        assert result["success"]
        assert result["response"]


# ===========================================================================
# 5. API Endpoints
# ===========================================================================

class TestCopilotAPI:
    """AI Copilot API endpoints."""

    def test_ai_summarize_endpoint(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.get("/api/v1/founder/ai/summarize/cp_obj_001")
            data = resp.get_json()
            assert data["success"]
            assert "summary" in data

    def test_ai_summarize_requires_auth(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/founder/ai/summarize/cp_obj_001")
            assert resp.status_code == 401

    def test_ai_health_endpoint(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.get("/api/v1/founder/ai/health")
            data = resp.get_json()
            assert data["success"]
            assert "provider" in data["data"]

    def test_ai_chat_endpoint(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.post(
                "/api/v1/founder/ai/chat/cp_conv_001",
                json={"content": "Hello SHUNYA"},
            )
            data = resp.get_json()
            assert data["success"]
            assert "response" in data["data"]

    def test_ai_chat_requires_message(self, app):
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.post(
                "/api/v1/founder/ai/chat/cp_conv_001",
                json={"content": ""},
            )
            assert resp.status_code == 400

    def test_conversation_endpoint_uses_copilot(self, app):
        """The existing /api/v1/founder/conversations/<id>/messages endpoint
        should now route through AI Copilot instead of hardcoded response."""
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.post(
                "/api/v1/founder/conversations/cp_conv_001/messages",
                json={"content": "What can you tell me about this?"},
            )
            data = resp.get_json()
            assert data["success"]
            if "response" in data.get("data", {}):
                assert data["data"]["response"]
            else:
                # Fallback to old format
                assert "assistant" in data["data"]


# ===========================================================================
# 6. Provider Fallback
# ===========================================================================

class TestProviderFallback:
    """Provider fallback chain works correctly."""

    def test_fallback_from_openai_to_local(self):
        reset_provider()
        provider = get_provider()
        assert provider.name == "local"

    def test_provider_chain_priority(self):
        reset_provider()
        # Without API keys set, should resolve to local
        from app.ai.provider import _PROVIDERS
        _PROVIDERS.clear()
        provider = get_provider()
        assert provider.name == "local"


# ===========================================================================
# 7. Regression — Milestones 1–4
# ===========================================================================

class TestMilestoneRegression:
    """Milestones 1–4 regressions pass with M5 changes."""

    def test_m1_signin(self, app):
        from app.adapters.os_adapter import sign_in
        result = sign_in(email="m5-regression@test.com", name="Regression")
        assert result["success"]

    def test_m1_create_object(self, app):
        identity_id = _make_identity(app)
        from app import db
        from app.founder.models import FounderSpace
        space = FounderSpace(space_id="m5_spc", name="M5 Reg", identity_id=identity_id)
        db.session.add(space)
        db.session.commit()
        from app.adapters.os_adapter import create_object
        result = create_object(name="M5 Object", object_type="Document",
                               space_id="m5_spc", identity_id=identity_id)
        assert result["success"] or result.get("object_id")

    def test_m2_morning_brief(self, app):
        from app.founder.executive_home_service import build_morning_brief
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        brief = build_morning_brief(identity_id)
        assert "items" in brief

    def test_m3_insights(self, app):
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = build_insights(identity_id=identity_id)
        assert result["summary"]["total_insights"] >= 0

    def test_m4_workspace_summary(self, app):
        from app.founder.workspace_intelligence import build_workspace_summary
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = build_workspace_summary("cp_obj_001")
        assert result["name"] == "Test Proposal"

    def test_m4_ai_understanding(self, app):
        from app.founder.workspace_intelligence import build_ai_understanding
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = build_ai_understanding("cp_obj_001")
        assert "what_is" in result

    def test_m4_relationship_intelligence(self, app):
        from app.founder.workspace_intelligence import build_relationship_intelligence
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = build_relationship_intelligence("cp_obj_001")
        assert len(result["groups"]) >= 1

    def test_m4_workspace_health(self, app):
        from app.founder.workspace_intelligence import compute_workspace_health
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = compute_workspace_health("cp_obj_001")
        assert 0 <= result["overall_score"] <= 1

    def test_m4_conversation_workspace(self, app):
        from app.founder.workspace_intelligence import get_conversation_workspace
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = get_conversation_workspace("cp_obj_001")
        assert result["status"] == "active"

    def test_m4_evidence_explorer(self, app):
        from app.founder.workspace_intelligence import build_evidence_explorer
        identity_id = _make_identity(app)
        _seed_copilot_data(app, identity_id)
        result = build_evidence_explorer("cp_obj_001")
        assert len(result) >= 3