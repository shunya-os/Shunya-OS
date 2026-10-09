"""G-stage — human context changes SHUNYA's behavior (the G2 requirement).

Human context is not implemented merely because a table exists: an explicitly
stated user circumstance must change a meaningful aspect of SHUNYA's behavior.
These tests pin the real effect chain:

  recorded explicit context (ACTIVE)
    -> build_human_context_guidance (tone/pacing/depth lines only)
    -> ContextFrame.human_context_guidance (context propagation)
    -> the reasoning prompt actually carries the guidance line.

Corrections and expirations are honoured by construction (only ACTIVE status
is read). Guidance never mixes into business facts and is never quoted back.
"""

import pytest


@pytest.fixture(scope="function")
def app():
    from app import create_app, db
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def _seed_person(email):
    from app import db
    from app.models import Person, PersonIdentity
    p = Person(canonical_name="Founder", tenant_id=989)
    db.session.add(p)
    db.session.flush()
    db.session.add(PersonIdentity(
        person_id=p.id, identity_type="email",
        identity_value=email, normalized_value=email.lower(),
    ))
    db.session.commit()
    return p.id


def _record(person_id, expression_type):
    from app.human_context.emotional import EmotionalContextService
    return EmotionalContextService().record(
        expression_type=expression_type, person_id=person_id,
        source="human", created_by="test")


def test_explicit_frustration_changes_behavior_guidance(app):
    from app.human_context.guidance import build_human_context_guidance

    pid = _seed_person("founder@example.com")
    _record(pid, "frustration")
    guidance = build_human_context_guidance("founder@example.com")
    assert guidance, "an explicit, active circumstance must produce guidance"
    assert "frustration" in guidance.lower()
    assert "patient" in guidance.lower()


def test_guidance_is_email_scoped_and_silent_without_context(app):
    from app.human_context.guidance import build_human_context_guidance

    _seed_person("founder@example.com")
    assert build_human_context_guidance("stranger@example.com") == ""
    assert build_human_context_guidance("") == ""


def test_correcting_context_changes_the_guidance_immediately(app):
    from app.human_context.emotional import EmotionalContextService
    from app.human_context.guidance import build_human_context_guidance

    pid = _seed_person("founder@example.com")
    rec = _record(pid, "uncertainty")
    assert "uncertainty" in build_human_context_guidance("founder@example.com").lower()

    # Correcting records a NEW active statement (the semantics of the
    # service: correction = updated truth, expire = revoked).
    svc = EmotionalContextService()
    svc.correct(rec["item_id"], corrected_by="test",
                new_expression_type="excitement",
                correction_note="User clarified they are excited, not unsure")
    guidance = build_human_context_guidance("founder@example.com")
    assert "excitement" in guidance.lower()
    assert "step by step" not in guidance.lower(), (
        "the superseded uncertainty guidance must not linger")


def test_expired_context_stops_affecting_behavior(app):
    from app.human_context.emotional import EmotionalContextService
    from app.human_context.guidance import build_human_context_guidance

    pid = _seed_person("founder@example.com")
    rec = _record(pid, "frustration")
    assert build_human_context_guidance("founder@example.com") != ""

    EmotionalContextService().expire(rec["item_id"])
    assert build_human_context_guidance("founder@example.com") == "", (
        "expired context must stop affecting behavior")


def test_at_most_two_guidance_lines(app):
    from app.human_context.guidance import build_human_context_guidance

    pid = _seed_person("founder@example.com")
    for et in ("frustration", "uncertainty", "urgent"):
        _record(pid, et)
    guidance = build_human_context_guidance("founder@example.com")
    hits = sum(1 for et in ("frustration", "uncertainty", "urgent")
               if et in guidance.lower())
    assert hits <= 2, f"too many guidance lines: {guidance}"


def test_context_frame_carries_the_guidance(app):
    from core.intelligence_runtime.context import ContextEngine

    reg = ContextEngine()
    reg.update("s1", human_context_guidance="be gentle")
    assert reg.get("s1").human_context_guidance == "be gentle"


def test_reasoning_prompt_actually_includes_the_guidance(app):
    """The behavioral effect: the LLM prompt carries the guidance, phrased as
    delivery guidance (never as a business fact)."""
    from core.intelligence_runtime.reasoning import ReasoningEngine
    from core.intelligence_runtime.types import ContextFrame, UserIntent

    captured = {}

    def fake_llm(messages, temperature=0.7, max_tokens=1024):
        captured["messages"] = messages
        return {"content": "ok"}

    engine = ReasoningEngine()
    engine.wire_llm_provider(fake_llm)
    ctx = ContextFrame(human_context_guidance=(
        "The user recently expressed frustration. Be patient and direct."))
    text = engine._generate_via_llm(UserIntent(raw_input="hello"), [], ctx)
    assert text == "ok"
    user_msg = captured["messages"][1]["content"]
    assert "Human context" in user_msg
    assert "Be patient" in user_msg
    assert "do not mention" in user_msg.lower()


def test_prompt_without_context_has_no_human_context_section(app):
    from core.intelligence_runtime.reasoning import ReasoningEngine
    from core.intelligence_runtime.types import ContextFrame, UserIntent

    captured = {}

    def fake_llm(messages, temperature=0.7, max_tokens=1024):
        captured["messages"] = messages
        return {"content": "ok"}

    engine = ReasoningEngine()
    engine.wire_llm_provider(fake_llm)
    engine._generate_via_llm(UserIntent(raw_input="hello"), [], ContextFrame())
    assert "Human context" not in captured["messages"][1]["content"]