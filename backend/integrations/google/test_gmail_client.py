"""Tests for gmail_client.py — all pure functions (no network)."""

from backend.integrations.google.gmail_client import (
    parse_message,
    decode_base64,
    extract_message_body,
    classify_email,
    detect_intent,
    extract_entities,
    clean_html,
)


# ═══════════════════════════════════════════
# decode_base64
# ═══════════════════════════════════════════

def test_decode_base64_plain_text():
    result = decode_base64("SGVsbG8gV29ybGQ=")
    assert result == "Hello World"


def test_decode_base64_utf8():
    encoded = "8J+Ygw=="
    result = decode_base64(encoded)
    assert result == "😃"


def test_decode_base64_empty():
    assert decode_base64("") == ""


def test_decode_base64_invalid_tolerates_garbage():
    result = decode_base64("!!!not-valid-base64!!!")
    assert result is not None
    assert isinstance(result, str)


# ═══════════════════════════════════════════
# HTML cleaning
# ═══════════════════════════════════════════

def test_clean_html_strips_tags():
    assert clean_html("<p>Hello</p>") == "Hello"


def test_clean_html_removes_scripts():
    result = clean_html("Hello<script>alert('xss')</script>World")
    assert result == "HelloWorld"


def test_clean_html_removes_styles():
    result = clean_html("Hello<style>body{color:red}</style>World")
    assert result == "HelloWorld"


def test_clean_html_converts_br_to_newlines():
    result = clean_html("Line1<br>Line2<br/>Line3")
    assert "Line1\nLine2\nLine3" in result


def test_clean_html_decodes_entities():
    result = clean_html("&amp; &lt; &gt; &quot; &nbsp;")
    assert "&" in result
    assert "<" in result
    assert ">" in result


def test_clean_html_empty():
    assert clean_html("") == ""


def test_clean_html_preserves_meaningful_text():
    html = "<h1>Title</h1><p>Paragraph with <b>bold</b> text.</p>"
    result = clean_html(html)
    assert "Title" in result
    assert "Paragraph" in result
    assert "bold" in result


# ═══════════════════════════════════════════
# extract_message_body — recursive MIME
# ═══════════════════════════════════════════

def test_direct_body():
    msg = {"payload": {"body": {"data": "SGVsbG8gRGlyZWN0"}}}
    assert extract_message_body(msg) == "Hello Direct"


def test_multipart_plain_text():
    msg = {
        "payload": {
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "UGxhaW4gVGV4dA=="}},
                {"mimeType": "text/html", "body": {"data": "PGgxPkhUTUw8L2gxPg=="}},
            ]
        }
    }
    assert extract_message_body(msg) == "Plain Text"


def test_multipart_fallback_cleaned_html():
    """HTML fallback must return cleaned text, not raw markup."""
    msg = {
        "payload": {
            "parts": [
                {"mimeType": "text/html", "body": {"data": "PGgxPkhUTUw8L2gxPg=="}},
            ]
        }
    }
    result = extract_message_body(msg)
    assert result is not None
    assert "HTML" in result
    assert "<h1>" not in result
    assert "<" not in result


def test_nested_multipart_alternative_plain():
    """multipart/alternative with text/plain inside."""
    msg = {
        "payload": {
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "TmVzdGVkIFBsYWlu"}},
                {"mimeType": "text/html", "body": {"data": "PGgxPkhUTUw8L2gxPg=="}},
            ],
        }
    }
    assert extract_message_body(msg) == "Nested Plain"


def test_nested_multipart_mixed():
    """multipart/mixed wrapping multipart/alternative."""
    msg = {
        "payload": {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": "RGVlcCBOZXN0ZWQ="}},
                    ],
                },
                {"mimeType": "application/octet-stream", "body": {}},
            ],
        }
    }
    assert extract_message_body(msg) == "Deep Nested"


def test_no_body_returns_none():
    msg = {"payload": {"body": {}}}
    assert extract_message_body(msg) is None


def test_nested_html_does_not_outrank_sibling_plain():
    """HTML inside a nested multipart must NOT outrank a sibling text/plain."""
    msg = {
        "payload": {
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "T3V0ZXIgUGxhaW4="}},
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/html", "body": {"data": "PGgxPklubmVyIEhUTUw8L2gxPg=="}},
                    ],
                },
            ],
        }
    }
    # "Outer Plain" must win over cleaned "Inner HTML"
    assert extract_message_body(msg) == "Outer Plain"


def test_deeply_nested_plain_outranks_html_another_branch():
    """Deeply nested text/plain must outrank HTML at a different branch."""
    msg = {
        "payload": {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {
                            "mimeType": "multipart/related",
                            "parts": [
                                {"mimeType": "text/html", "body": {"data": "PGgxPkRlZXAgSFRNTDwvaDE+"}},
                            ],
                        },
                    ],
                },
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": "RGVlcCBOZXN0ZWQgUGxhaW4="}},
                    ],
                },
            ],
        }
    }
    assert extract_message_body(msg) == "Deep Nested Plain"


def test_deeply_nested_html_returned_when_no_plain():
    """Deeply nested HTML must be returned cleaned when no plain text exists."""
    msg = {
        "payload": {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {
                            "mimeType": "multipart/related",
                            "parts": [
                                {"mimeType": "text/html", "body": {"data": "PGgxPkRlZXAgSFRNTDwvaDE+"}},
                            ],
                        },
                    ],
                },
            ],
        }
    }
    result = extract_message_body(msg)
    assert result is not None
    assert "Deep HTML" in result
    assert "<h1>" not in result


# ═══════════════════════════════════════════
# classify_email
# ═══════════════════════════════════════════

def test_classify_payment():
    assert classify_email("Invoice", "Payment of ₹1000")["type"] == "payment"
    assert classify_email("Receipt", "receipt for transaction")["type"] == "payment"


def test_classify_lead():
    assert classify_email("Booking Confirmed", "Your trip to Goa")["type"] == "lead"
    assert classify_email("Flight", "flight itinerary")["type"] == "lead"


def test_classify_supplier():
    assert classify_email("Vendor Quote", "proposal for")["type"] == "supplier"
    assert classify_email("Partnership", "collaboration opportunity")["type"] == "supplier"


def test_classify_system():
    assert classify_email("Account Settings", "no-reply@google.com")["type"] == "system"
    assert classify_email("Security Alert", "verify your account")["type"] == "system"


def test_classify_unknown():
    assert classify_email("Random News", "Check out this article")["type"] == "unknown"


# ═══════════════════════════════════════════
# detect_intent
# ═══════════════════════════════════════════

def test_intent_travel():
    assert detect_intent("Plan trip to Goa packages and cost") == "travel_inquiry"


def test_intent_payment():
    assert detect_intent("Invoice payment of ₹5000 received") == "payment"


def test_intent_booking():
    assert detect_intent("Booking confirmed for your reservation") == "booking"
    assert detect_intent("Your itinerary is ready") == "booking"


def test_intent_system():
    assert detect_intent("Welcome to Google verify your account") == "system_notification"


def test_intent_business():
    assert detect_intent("Quote for partnership proposal") == "business_inquiry"


def test_intent_unknown():
    assert detect_intent("Nothing relevant here") == "unknown"


# ═══════════════════════════════════════════
# extract_entities
# ═══════════════════════════════════════════

def test_entities_extracts_dates():
    ents = extract_entities("Meeting on 2024-03-15 and also Mar 20, 2024")
    assert any("2024-03-15" in d or "2024" in d for d in ents["dates"])
    assert any("Mar 20, 2024" in d or "20" in d for d in ents["dates"])


def test_entities_extracts_destinations():
    ents = extract_entities("Going to Goa for vacation in Mumbai for meeting")
    assert any("Goa" in d for d in ents["destinations"])
    assert any("Mumbai" in d for d in ents["destinations"])


def test_entities_extracts_amounts():
    ents = extract_entities("Paid ₹1,000 for service and $50 for fees")
    assert any("₹1,000" in a for a in ents["amounts"])
    assert any("$50" in a for a in ents["amounts"])


def test_entities_deduplicates():
    ents = extract_entities("to Goa and to Goa")
    goa_count = sum(1 for d in ents["destinations"] if "Goa" in d)
    assert goa_count == 1


def test_entities_empty():
    ents = extract_entities("")
    assert ents == {"dates": [], "destinations": [], "amounts": []}


# ═══════════════════════════════════════════
# Header robustness
# ═══════════════════════════════════════════

def test_parse_message_case_insensitive_headers():
    """Header lookup must be case-insensitive."""
    msg = {
        "payload": {
            "headers": [
                {"name": "from", "value": "alice@example.com"},
                {"name": "SUBJECT", "value": "Hello"},
                {"name": "date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
            ],
            "body": {"data": "SGVsbG8="},
        }
    }
    result = parse_message(msg)
    assert result["from"] == "alice@example.com"
    assert result["subject"] == "Hello"


def test_parse_message_malformed_header_skipped():
    """Missing name or value in a header entry must not crash."""
    msg = {
        "payload": {
            "headers": [
                {"name": "From", "value": "alice@example.com"},
                {"notname": "To"},             # malformed — no name key
                {"name": "Subject"},            # malformed — no value key
                {"name": "Date", "value": "today"},
            ],
            "body": {"data": "SGVsbG8="},
        }
    }
    result = parse_message(msg)
    assert result["from"] == "alice@example.com"
    assert result["subject"] == ""
    assert result["date"] == "today"


def test_parse_message_missing_headers_returns_empty():
    """When no matching header exists, return empty string."""
    msg = {
        "payload": {
            "headers": [],
            "body": {"data": "SGVsbG8="},
        }
    }
    result = parse_message(msg)
    assert result["from"] == ""
    assert result["subject"] == ""
    assert result["body"] == "Hello"


# ═══════════════════════════════════════════
# Single body extraction — body reused across all fields
# ═══════════════════════════════════════════

def test_parse_message_body_extracted_once():
    """parse_message must extract body once and reuse it."""
    msg = {
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Booking Confirmed"},
            ],
            "body": {"data": "WW91ciB0cmlwIHRvIEdvYSBpcyBjb25maXJtZWQuIEJvb2tpbmcgIzEyMzQ1"},
        },
    }
    result = parse_message(msg)
    assert result["body"] == "Your trip to Goa is confirmed. Booking #12345"
    assert result["classification"]["type"] == "lead"
    assert result["intent"] == "booking"


# ═══════════════════════════════════════════
# parse_message (integration of all layers)
# ═══════════════════════════════════════════

def test_parse_message_full_pipeline():
    msg = {
        "id": "abc123",
        "threadId": "thr456",
        "payload": {
            "headers": [
                {"name": "From", "value": "alice@example.com"},
                {"name": "To", "value": "bob@example.com, carol@example.com"},
                {"name": "Subject", "value": "Booking Confirmed"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
            ],
            "body": {"data": "WW91ciB0cmlwIHRvIEdvYSBpcyBjb25maXJtZWQuIEJvb2tpbmcgIzEyMzQ1"},
        },
    }
    result = parse_message(msg)
    assert result["id"] == "abc123"
    assert result["subject"] == "Booking Confirmed"
    assert result["classification"]["type"] == "lead"
    assert result["intent"] == "booking"
    assert "Goa" in str(result["entities"]["destinations"])


def test_parse_message_empty_body():
    msg = {"id": "x", "threadId": "y", "payload": {"headers": [], "body": {}}}
    result = parse_message(msg)
    assert result["classification"]["type"] == "unknown"
    assert result["intent"] == "unknown"
    assert result["entities"] == {"dates": [], "destinations": [], "amounts": []}