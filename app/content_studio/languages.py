"""SHUNYA — Canonical Output Language Registry (R6B-2.7 Window 6 §7–§9).

Single source of truth for the languages SHUNYA can generate content in.
Components must NOT scatter language strings: they read this registry (the API
exposes it at ``GET /api/v1/content/languages``).

Rules encoded here:
  * ``auto`` means SHUNYA may INFER the language from explicit user context;
    when there is insufficient evidence it defaults to English (§8).
  * An explicit user selection is AUTHORITATIVE and must never be overridden.
  * ``hinglish`` means natural Hindi + English in ROMAN script — never
    Devanagari — and the generated content itself must be in that language
    (§9). This is a generation constraint, not a UI translation.
"""
from __future__ import annotations

import re
from typing import Any, Optional

#: Sentinel meaning "let SHUNYA infer from context".
AUTO = "auto"

#: Language used when Auto cannot infer from sufficient evidence.
DEFAULT_LANGUAGE = "en"

#: code -> (English label, native label, model instruction)
_LANGUAGES: dict[str, tuple[str, str, str]] = {
    "en": ("English", "English", "Write the entire output in English."),
    "hi": ("Hindi", "हिन्दी", "Write the entire output in Hindi using Devanagari script. Use natural, fluent Hindi."),
    "hinglish": ("Hinglish", "Hinglish", "Write the entire output in Hinglish: natural conversational Hindi and English mixed together, written ONLY in Roman script. Do NOT use Devanagari script anywhere. Example style: 'Yeh product bahut useful hai, aap isse easily use kar sakte hain.'"),
    "bn": ("Bengali", "বাংলা", "Write the entire output in Bengali using Bengali script."),
    "mr": ("Marathi", "मराठी", "Write the entire output in Marathi using Devanagari script."),
    "gu": ("Gujarati", "ગુજરાતી", "Write the entire output in Gujarati using Gujarati script."),
    "ta": ("Tamil", "தமிழ்", "Write the entire output in Tamil using Tamil script."),
    "te": ("Telugu", "తెలుగు", "Write the entire output in Telugu using Telugu script."),
    "kn": ("Kannada", "ಕನ್ನಡ", "Write the entire output in Kannada using Kannada script."),
    "ml": ("Malayalam", "മലയാളം", "Write the entire output in Malayalam using Malayalam script."),
    "pa": ("Punjabi", "ਪੰਜਾਬੀ", "Write the entire output in Punjabi using Gurmukhi script."),
    "ur": ("Urdu", "اردو", "Write the entire output in Urdu using Urdu script, right to left."),
    "fr": ("French", "Français", "Write the entire output in French."),
    "de": ("German", "Deutsch", "Write the entire output in German."),
    "es": ("Spanish", "Español", "Write the entire output in Spanish."),
    "it": ("Italian", "Italiano", "Write the entire output in Italian."),
    "pt": ("Portuguese", "Português", "Write the entire output in Portuguese."),
    "ja": ("Japanese", "日本語", "Write the entire output in Japanese, using appropriate Japanese script (kanji/kana)."),
    "ko": ("Korean", "한국어", "Write the entire output in Korean using Hangul."),
    "ar": ("Arabic", "العربية", "Write the entire output in Arabic, right to left."),
}

#: Codes whose scripts are non-Latin — used to reject a script mismatch.
_NON_LATIN = {"hi", "bn", "mr", "gu", "ta", "te", "kn", "ml", "pa", "ur", "ja", "ko", "ar"}

_NAME_TO_CODE = {
    "english": "en", "hindi": "hi", "hinglish": "hinglish", "bengali": "bn",
    "marathi": "mr", "gujarati": "gu", "tamil": "ta", "telugu": "te",
    "kannada": "kn", "malayalam": "ml", "punjabi": "pa", "urdu": "ur",
    "french": "fr", "german": "de", "spanish": "es", "italian": "it",
    "portuguese": "pt", "japanese": "ja", "korean": "ko", "arabic": "ar",
}

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def supported_codes() -> list[str]:
    """All selectable codes including ``auto``."""
    return [AUTO, *_LANGUAGES.keys()]


def is_supported(code: Any) -> bool:
    """True when ``code`` is a recognised language identifier."""
    return normalize(code) is not None


def normalize(code: Any) -> Optional[str]:
    """Canonicalise a client-supplied language value.

    Accepts a registry code (``hi``) or a display name (``Hindi``).
    Returns None for anything unsupported — callers MUST fail closed.
    """
    if not isinstance(code, str):
        return None
    value = code.strip()
    if not value:
        return None
    lowered = value.lower()
    if lowered == AUTO:
        return AUTO
    if lowered in _LANGUAGES:
        return lowered
    if lowered in _NAME_TO_CODE:
        return _NAME_TO_CODE[lowered]
    return None


def label(code: str) -> str:
    return _LANGUAGES.get(code, ("Unknown", "Unknown", ""))[0]


def language_prompt(code: str) -> str:
    """The generation constraint instruction for a resolved language."""
    if code == AUTO:
        code = DEFAULT_LANGUAGE
    return _LANGUAGES.get(code, _LANGUAGES[DEFAULT_LANGUAGE])[2]


def registry() -> list[dict[str, str]]:
    """Serialisable registry for the API/UI (codes + labels, no logic)."""
    rows = [{"code": AUTO, "label": "Auto", "native": "Auto",
             "hint": "Let SHUNYA infer the language from your input."}]
    for code, (eng, native, _instr) in _LANGUAGES.items():
        rows.append({"code": code, "label": eng, "native": native, "hint": ""})
    return rows


def resolve_output_language(
    requested: Any,
    context_text: str = "",
) -> tuple[str, str]:
    """Resolve the effective output language.

    Returns ``(language_code, source)`` where source is one of
    ``explicit`` | ``inferred`` | ``default``.

    An explicit, supported selection is AUTHORITATIVE and is never overridden.
    ``auto`` infers from explicit user context; with insufficient evidence it
    falls back to English (§8).
    """
    normalized = normalize(requested)

    # Unsupported value supplied by the client → fail closed to the default,
    # never a silent pass-through of an arbitrary string.
    if normalized is None:
        return DEFAULT_LANGUAGE, "default"

    if normalized != AUTO:
        return normalized, "explicit"

    inferred = infer_language(context_text)
    if inferred:
        return inferred, "inferred"
    return DEFAULT_LANGUAGE, "default"


def infer_language(text: str) -> Optional[str]:
    """Infer a language from explicit user context. Conservative by design."""
    if not text or not text.strip():
        return None
    if _DEVANAGARI.search(text):
        return "hi"
    lowered = text.lower()
    # Explicit natural-language requests are the strongest evidence.
    for name, code in _NAME_TO_CODE.items():
        if re.search(rf"\b(?:in|write in|output in|language)\s+{name}\b", lowered):
            return code
    return None


def script_mismatch(language: str, content: str) -> bool:
    """True when generated output violates the requested script.

    The sharpest case: Hinglish must be Roman script — Devanagari output is a
    failure, not a stylistic difference (§9).
    """
    if not content:
        return False
    if language == "hinglish":
        return bool(_DEVANAGARI.search(content))
    if language in _NON_LATIN:
        return False  # script presence is checked by the provider, not here
    return False
