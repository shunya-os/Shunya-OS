import base64
import os
import re
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from backend.core.email.email_mapper import map_to_email_entity
from backend.core.email.email_store import save_email

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_gmail_service():
    token_file = os.environ.get("GOOGLE_TOKEN_FILE")

    if not token_file or not os.path.exists(token_file):
        raise Exception("❌ GOOGLE_TOKEN_FILE not set or file missing")

    creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    return build("gmail", "v1", credentials=creds)


def fetch_recent_threads(max_results=5):
    service = get_gmail_service()

    results = service.users().threads().list(
        userId="me",
        maxResults=max_results
    ).execute()

    threads = results.get("threads", [])

    print("\n=== THREADS ===")
    for t in threads:
        print(t["id"])

    return threads


def get_thread_messages(thread_id):
    service = get_gmail_service()

    thread = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full"
    ).execute()

    return thread.get("messages", [])


def decode_base64(data):
    try:
        decoded = base64.urlsafe_b64decode(data.encode("UTF-8"))
        return decoded.decode("utf-8", errors="ignore")
    except Exception:
        return None


# ── HTML cleaning (no external dependencies) ──

_HTML_TAG_RE = re.compile(r"<[^>]*>")
_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL
)
_ENTITY_RE = re.compile(r"&(?:amp|lt|gt|quot|nbsp|#\d+);")
_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_P_RE = re.compile(r"</?p[^>]*>", re.IGNORECASE)
_DIV_RE = re.compile(r"</?div[^>]*>", re.IGNORECASE)
_LI_RE = re.compile(r"</?li[^>]*>", re.IGNORECASE)
_TR_RE = re.compile(r"</?tr[^>]*>", re.IGNORECASE)
_NL_RE = re.compile(r"\n{3,}")


def clean_html(html_text: str) -> str:
    if not html_text:
        return ""

    # Remove script and style blocks
    text = _SCRIPT_STYLE_RE.sub("", html_text)

    # Block-level tags → newline
    text = _BR_RE.sub("\n", text)
    text = re.sub(r"</?p[^>]*>", "\n", text)
    text = re.sub(r"</?div[^>]*>", "\n", text)
    text = re.sub(r"</?li[^>]*>", "\n", text)
    text = re.sub(r"</?tr[^>]*>", "\n", text)
    text = re.sub(r"</?td[^>]*>", " ", text)

    # Strip remaining tags
    text = _HTML_TAG_RE.sub("", text)

    # Decode common entities
    text = _ENTITY_RE.sub(_decode_entity, text)

    # Collapse excessive whitespace
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = _NL_RE.sub("\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = text.strip()

    return text


def _decode_entity(m):
    val = m.group(0)
    return {
        "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&nbsp;": " ",
    }.get(val, _decode_numeric(val))


def _decode_numeric(val):
    m = re.match(r"&#(\d+);", val)
    if m:
        try:
            return chr(int(m.group(1)))
        except (ValueError, OverflowError):
            pass
    return val


# ── Recursive MIME body extraction ──

def extract_message_body(msg):
    """Recursively extract the best readable body from a Gmail message payload.

    Preference: text/plain > cleaned text/html > None.
    Handles multipart/alternative, multipart/mixed, and nested multipart.
    """
    payload = msg.get("payload", {})
    plain_text, html_text = _extract_from_payload(payload)
    return plain_text or html_text


def _extract_from_payload(payload):
    """Recursive helper returning (plain_text, html_text) tuple.

    plain_text: decoded text/plain content (preferred).
    html_text:  cleaned text/html content (fallback).
    Either or both may be None.
    The top-level caller applies the text/plain > html > None precedence.
    """
    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    # ── Leaf: text/plain ──
    if mime == "text/plain":
        if body_data:
            return (decode_base64(body_data), None)
        return (None, None)

    # ── Leaf: text/html ──
    if mime == "text/html":
        if body_data:
            return (None, clean_html(decode_base64(body_data) or ""))
        return (None, None)

    # ── Container with direct body data (no MIME, or unknown MIME) ──
    if body_data:
        text = decode_base64(body_data)
        if text:
            # Heuristic: if the decoded text contains HTML tags, treat as html
            if "<" in text and ">" in text:
                return (None, clean_html(text))
            return (text, None)

    # ── Recurse into child parts ──
    parts = payload.get("parts", [])
    if not parts:
        return (None, None)

    best_plain = None
    best_html = None

    for part in parts:
        part_mime = part.get("mimeType", "")

        if part_mime == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                best_plain = decode_base64(data)
                break  # text/plain is globally optimal — stop scanning

        elif part_mime == "text/html":
            data = part.get("body", {}).get("data")
            if data and best_html is None:
                best_html = clean_html(decode_base64(data) or "")

        else:
            # Recurse — could be multipart/* or unknown type with nested parts
            p, h = _extract_from_payload(part)
            if p and best_plain is None:
                best_plain = p
            if h and best_html is None:
                best_html = h

    return (best_plain, best_html)


# ── Email Intelligence Extraction (Level 1) ──

def classify_email(subject, body):
    text = f"{subject or ''} {body or ''}".lower()

    if any(kw in text for kw in [
        "payment", "invoice", "receipt", "billing",
        "paid", "transaction", "amount due",
    ]):
        return {"type": "payment"}
    if any(kw in text for kw in [
        "booking confirmed", "reservation", "itinerary",
        "your trip", "flight", "hotel booking",
    ]):
        return {"type": "lead"}
    if any(kw in text for kw in [
        "quote", "proposal", "supplier", "vendor",
        "partnership", "collaboration",
    ]):
        return {"type": "supplier"}
    if any(kw in text for kw in [
        "no-reply", "notification", "alert",
        "account settings", "verify", "security",
    ]):
        return {"type": "system"}

    return {"type": "unknown"}


def detect_intent(body):
    text = (body or "").lower()

    if any(kw in text for kw in [
        "plan trip", "package", "cost", "destination",
        "travel", "flight", "hotel", "vacation",
    ]):
        return "travel_inquiry"
    if any(kw in text for kw in [
        "invoice", "payment", "paid", "receipt",
        "amount", "billing", "transaction",
    ]):
        return "payment"
    if any(kw in text for kw in [
        "booking confirmed", "confirmed", "reservation",
        "booked", "itinerary",
    ]):
        return "booking"
    if any(kw in text for kw in [
        "welcome", "verify", "setup", "security",
        "notification", "alert",
    ]):
        return "system_notification"
    if any(kw in text for kw in [
        "quote", "proposal", "partnership", "supplier",
        "vendor", "collaboration",
    ]):
        return "business_inquiry"

    return "unknown"


def extract_entities(body):
    text = body or ""
    entities = {"dates": [], "destinations": [], "amounts": []}

    # Dates
    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        (
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"[a-z]* \d{1,2},?\s*\d{4}\b"
        ),
        (
            r"\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|"
            r"Oct|Nov|Dec)[a-z]* \d{4}\b"
        ),
        (
            r"\b(?:january|february|march|april|may|june|july|"
            r"august|september|october|november|december)"
            r" \d{1,2},?\s*\d{4}\b"
        ),
    ]
    for pat in date_patterns:
        entities["dates"].extend(re.findall(pat, text, re.IGNORECASE))

    # Destinations
    dest_keywords = [
        r"(?<=\bto\s)[A-Z][a-z]+(?:\s[A-Z][a-z]+)*",
        r"(?<=\bin\s)[A-Z][a-z]+(?:\s[A-Z][a-z]+)*",
    ]
    for pat in dest_keywords:
        entities["destinations"].extend(re.findall(pat, text))

    # Amounts
    amount_patterns = [
        r"[₹\$€£]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?",
        (
            r"\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*"
            r"(?:USD|EUR|GBP|INR|dollars|rupees)"
        ),
    ]
    for pat in amount_patterns:
        entities["amounts"].extend(re.findall(pat, text, re.IGNORECASE))

    # Deduplicate
    for key in entities:
        seen = set()
        deduped = []
        for item in entities[key]:
            norm = item.lower().strip()
            if norm not in seen:
                seen.add(norm)
                deduped.append(item)
        entities[key] = deduped

    return entities


def parse_message(msg):
    """Parse a Gmail message into structured dict with single body extraction."""
    headers = msg.get("payload", {}).get("headers", [])

    def get_header(name):
        name_lower = name.lower()
        for h in headers:
            if isinstance(h, dict) and h.get("name", "").lower() == name_lower:
                return h.get("value")
        return None

    body = extract_message_body(msg)

    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "from": get_header("From") or "",
        "to": get_header("To") or "",
        "subject": get_header("Subject") or "",
        "date": get_header("Date"),
        "body": body or "",
        "classification": classify_email(
            get_header("Subject") or "", body
        ),
        "intent": detect_intent(body),
        "entities": extract_entities(body),
    }


if __name__ == "__main__":
    threads = fetch_recent_threads(2)

    for t in threads:
        msgs = get_thread_messages(t["id"])
        parsed = [parse_message(m) for m in msgs]

        print("\n=== THREAD ===")
        for p in parsed:
            entity = map_to_email_entity(p)
            save_email(entity)
            print(f"[STORED] TYPE: {entity.type} | INTENT: {entity.intent} | THREAD: {entity.thread_id}")

            print("\nFROM:", p["from"])
            print("SUBJECT:", p["subject"])
            print("BODY:", (p["body"] or "")[:500])
            cls = p.get("classification", {})
            print("TYPE:", cls.get("type", "unknown"))
            print("INTENT:", p.get("intent", "unknown"))
            ents = p.get("entities", {})
            print("DESTINATIONS:", ents.get("destinations", []))
            print("DATES:", ents.get("dates", []))
            print("AMOUNT:", ents.get("amounts", []))