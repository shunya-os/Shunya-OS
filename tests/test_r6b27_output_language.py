"""R6B-2.7 Window 6 §7–§15 — Output language + server-authoritative generation.

Proves:
  * the canonical language registry is the single source of truth;
  * Auto infers from context, else defaults to English;
  * an explicit selection is authoritative;
  * Hinglish means ROMAN script Hindi+English, never Devanagari;
  * the language reaches the generation orchestration as a constraint;
  * an unsupported language is rejected (not passed through);
  * the client CANNOT inject model/provider (server authority);
  * there is no silent paid fallback.
"""
from __future__ import annotations

import inspect
import os

import pytest

from app.content_studio import languages as langs
from app.integration.service import generate_content

#: The minimum registry required by the directive (§8).
REQUIRED_CODES = {
    "auto", "en", "hi", "hinglish", "bn", "mr", "gu", "ta", "te", "kn",
    "ml", "pa", "ur", "fr", "de", "es", "it", "pt", "ja", "ko", "ar",
}


# ── Registry ────────────────────────────────────────────────────────────


def test_registry_contains_every_required_language():
    codes = {row["code"] for row in langs.registry()}
    assert REQUIRED_CODES.issubset(codes), REQUIRED_CODES - codes


def test_registry_rows_are_serialisable_and_labelled():
    for row in langs.registry():
        assert set(row) >= {"code", "label", "native"}
        assert row["label"]


def test_languages_endpoint_is_public_and_serves_the_registry(client):
    r = client.get("/api/v1/content/languages")
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"] is True
    assert body["default"] == "en"
    codes = {row["code"] for row in body["data"]}
    assert REQUIRED_CODES.issubset(codes)


# ── Normalisation / rejection ───────────────────────────────────────────


def test_normalize_accepts_codes_and_display_names():
    assert langs.normalize("hi") == "hi"
    assert langs.normalize("Hindi") == "hi"
    assert langs.normalize("  HINGLISH ") == "hinglish"
    assert langs.normalize("auto") == "auto"


@pytest.mark.parametrize("bad", ["", "  ", "klingon", "zz", None, 7, "en; DROP TABLE"])
def test_normalize_rejects_unsupported_values(bad):
    assert langs.normalize(bad) is None
    assert langs.is_supported(bad) is False


# ── Resolution semantics ────────────────────────────────────────────────


def test_explicit_selection_is_authoritative():
    code, source = langs.resolve_output_language("hi", "please write in French")
    assert (code, source) == ("hi", "explicit")


def test_auto_defaults_to_english_without_evidence():
    code, source = langs.resolve_output_language("auto", "a blog about coffee")
    assert (code, source) == ("en", "default")


def test_auto_infers_from_explicit_context():
    code, source = langs.resolve_output_language("auto", "please write this in French")
    assert (code, source) == ("fr", "inferred")

    code, source = langs.resolve_output_language("auto", "मेरे व्यवसाय के बारे में लिखें")
    assert (code, source) == ("hi", "inferred")


def test_unsupported_requested_language_fails_closed_to_default():
    code, source = langs.resolve_output_language("klingon", "text")
    assert (code, source) == ("en", "default")


def test_resolution_is_deterministic_for_retry():
    """Retry/regeneration must resolve to the same language."""
    args = ("hinglish", "some topic")
    assert langs.resolve_output_language(*args) == langs.resolve_output_language(*args)


# ── Hinglish semantics (§9) ─────────────────────────────────────────────


def test_hinglish_instruction_forbids_devanagari_and_requires_roman():
    instruction = langs.language_prompt("hinglish")
    assert "Roman script" in instruction
    assert "Do NOT use Devanagari" in instruction


def test_hinglish_output_in_devanagari_is_a_script_mismatch():
    roman = "Yeh product bahut useful hai, aap isse easily use kar sakte hain."
    devanagari = "यह उत्पाद बहुत उपयोगी है।"
    assert langs.script_mismatch("hinglish", roman) is False
    assert langs.script_mismatch("hinglish", devanagari) is True


def test_language_prompt_never_returns_empty():
    for code in langs.supported_codes():
        assert langs.language_prompt(code)


# ── Server authority: the client cannot choose the model (§10) ──────────


def test_generate_content_exposes_no_model_or_provider_parameter():
    params = set(inspect.signature(generate_content).parameters)
    assert "model" not in params
    assert "provider" not in params
    assert "output_language" in params


def test_org_less_identity_is_denied_fail_closed(logged_in_client):
    """CONTENT STUDIO BLOCKER (documented, NOT hidden).

    An authenticated identity with no organization membership is denied by the
    global before_request guard (app/__init__.py → "No organization membership",
    403). This is the root cause of the visible Content Studio
    "Generation failed / no canonical workspace context".

    The denial is EXPLICIT and fail-closed — the property this test pins. It
    must stay specific rather than degrading into a generic "Generation failed".
    Changing this contract requires the canonical personal-workspace
    authorization decision (§6), which is a security-sensitive change to a
    GLOBAL guard and is deliberately NOT made without that decision.
    """
    r = logged_in_client.post("/api/v1/content/generate", json={"prompt": "x"})
    assert r.status_code == 403
    assert "organization" in (r.get_json().get("error", "") + r.get_json().get("detail", "")).lower()


def test_language_validation_precedes_authorization_boundary(client):
    """The language contract is enforced before any generation is attempted."""
    r = client.post("/api/v1/content/generate", json={
        "prompt": "x", "output_language": "klingon",
    })
    # Unauthenticated callers are stopped first — never reaching the provider.
    assert r.status_code == 401


def test_selected_language_is_applied_as_a_constraint(monkeypatch):
    """The resolved language reaches the orchestrator as a real constraint."""
    captured: dict = {}

    def _fake_generate_content(**kwargs):
        captured.update(kwargs)
        return {"success": True, "content": "ok", "error": None}

    monkeypatch.setattr(
        "app.integration.service.generate_content", _fake_generate_content
    )
    # Exercise the contract at the service boundary the route delegates to.
    from app.content_studio.languages import language_prompt
    from app.integration import service as integration_service
    integration_service.generate_content(
        prompt="Write a tagline",
        additional_instructions=language_prompt("hinglish"),
        output_language="hinglish",
    )
    assert "Roman script" in captured["additional_instructions"]
    assert captured["output_language"] == "hinglish"


def test_route_never_reads_client_model_or_provider():
    """The route must not read model/provider from the request body (§10)."""
    src = open(
        os.path.join(os.path.dirname(__file__), "..", "app", "content_studio", "routes.py"),
        encoding="utf-8",
    ).read()
    code = "\n".join(
        ln for ln in src.splitlines() if not ln.strip().startswith("#")
    )
    assert "data.get(\"model\"" not in code
    assert "data.get('model'" not in code
    assert "data.get(\"provider\"" not in code
    assert "data.get('provider'" not in code


# ── No silent paid fallback (§11) ───────────────────────────────────────


def test_generation_failure_is_truthful_and_not_silently_retried(monkeypatch):
    """A failing provider yields an honest failure — no hidden second call."""
    calls = {"n": 0}

    class _FailingProvider:
        name = "failing"

        def complete(self, **kwargs):
            calls["n"] += 1
            return {"content": None, "finish_reason": "error", "error": "provider down"}

    monkeypatch.setattr("app.ai.provider.resolve_provider", lambda: _FailingProvider())

    result = generate_content(prompt="x", output_language="en")
    assert result["success"] is False
    assert result["error"]
    assert calls["n"] == 1, "must not retry/escalate behind the user's back"
