"""
SHUNYA OS — Telegram Integration

Bot token management, webhook registration, inquiry parsing,
outbound messaging, and dashboard summary engine.
"""

import os
import re
import json
from datetime import datetime
from typing import Optional

from app import db
from app.models import next_inquiry_code
from sqlalchemy import func

# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "telegram_bot_token.txt")


def _read_token_file() -> str:
    """Read bot token from file storage."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return ""


def _write_token_file(token: str):
    """Persist bot token to file storage."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token.strip())


def save_telegram_token(token: str):
    """Validate and save a Telegram bot token."""
    token = token.strip()
    if not token:
        raise ValueError("Empty token")
    _write_token_file(token)


def get_telegram_token() -> str:
    """Get bot token from env var (first) or file (fallback)."""
    return os.getenv("TELEGRAM_BOT_TOKEN") or _read_token_file()


# ---------------------------------------------------------------------------
# Bot API helpers
# ---------------------------------------------------------------------------

def _bot_api(method: str, token: str, payload: dict | None = None, timeout: int = 15):
    """Call Telegram Bot API method with error handling."""
    try:
        import requests
    except ImportError:
        return {"ok": False, "description": "requests library not available"}

    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        r = requests.post(url, json=payload or {}, timeout=timeout)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


def verify_token(token: str) -> tuple[bool, str]:
    """Check if a bot token is valid via getMe API."""
    data = _bot_api("getMe", token)
    if data.get("ok"):
        bot = data.get("result", {})
        return True, f"@{bot.get('username', 'unknown')}"
    return False, data.get("description", "Invalid token")


def get_webhook_info(token: str) -> dict:
    """Get current webhook status from Telegram."""
    data = _bot_api("getWebhookInfo", token)
    return data.get("result", {})


def set_telegram_webhook(token: str, url: str) -> tuple[bool, str]:
    """Register or update the Telegram webhook URL."""
    data = _bot_api("setWebhook", token, {"url": url, "max_connections": 40})
    if data.get("ok"):
        return True, url
    return False, data.get("description", str(data))


def delete_webhook(token: str) -> tuple[bool, str]:
    """Remove the current webhook."""
    data = _bot_api("deleteWebhook", token)
    return data.get("ok", False), "deleted" if data.get("ok") else data.get("description", "")


def send_message(token: str, chat_id: str, text: str, parse_mode: str = "") -> bool:
    """Send a message to a Telegram chat."""
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    data = _bot_api("sendMessage", token, payload)
    return data.get("ok", False)


def set_bot_commands(token: str) -> bool:
    """Register bot command menu for the team."""
    commands = [
        {"command": "start", "description": "Welcome & instructions"},
        {"command": "lead", "description": "Log a new inquiry (e.g. /lead Bali 3 nights 2 adults)"},
        {"command": "status", "description": "Check bot status"},
        {"command": "help", "description": "Show available commands"},
    ]
    data = _bot_api("setMyCommands", token, {"commands": commands})
    return data.get("ok", False)


# ---------------------------------------------------------------------------
# Inquiry text parser
# ---------------------------------------------------------------------------

def parse_inquiry_text(text: str) -> dict:
    """
    Extract structured travel info from free-text inquiry.

    Input: "3 nights Bali for 2 adults 15 Dec honeymoon"
    Output: {destination, nights, adults, kids, dates, name, budget, occasion}
    """
    text = text.strip()
    result = {
        "destination": None,
        "nights": None,
        "adults": None,
        "kids": None,
        "dates": None,
        "name": None,
        "budget": None,
        "occasion": None,
    }

    # --- Destination ---
    # "3 nights Bali for 2 adults" → Bali
    # "trip to Bali" → Bali
    # "Bali for 2" → Bali (PlaceName before "for")
    # "Goa for 2 adults" → Goa
    # "to Bali for 2 adults" → Bali
    # "Kerala 5 nights 2 adults" → Kerala (PlaceName at start, before nights)
    # "family trip Sri Lanka 4 nights" → Sri Lanka
    m = re.search(r"(?i)(\d+\s*nights?\s+)([A-Z][a-zA-Z\s]{2,30}?)(?:\s+for\s|\s+in\s|$)", text)
    if m:
        result["destination"] = m.group(2).strip()
    else:
        m = re.search(r"(?i)(?:to|in|for)\s+([A-Z][a-zA-Z\s]{2,30}?)(?:\s+\d|$)", text)
        if m:
            result["destination"] = m.group(1).strip()
        else:
            m = re.search(r"(?i)([A-Z][a-zA-Z]+)\s+for\s+\d", text)
            if m:
                result["destination"] = m.group(1).strip()
            else:
                # "family trip Sri Lanka" → PlaceName after "trip" (check before name+nights to avoid false match)
                m = re.search(r"(?i)(?:trip|visit)\s+(?:to\s+)?([A-Z][a-zA-Z\s]{2,30}?)(?:\s+\d|$)", text)
                if m:
                    result["destination"] = m.group(1).strip()
                else:
                    # "Kerala 5 nights" → PlaceName before nights
                    m = re.search(r"(?i)^([A-Z][a-zA-Z]{2,30}?)\s+\d+\s+night", text)
                    if m:
                        result["destination"] = m.group(1).strip()
                    else:
                        # Fallback: first capitalized word after "to/in/for"
                        m = re.search(r"(?i)(?:to|in|for)\s+([A-Z][a-zA-Z]+)", text)
                        if m:
                            result["destination"] = m.group(1)

    # --- Nights ---
    m = re.search(r"(\d+)\s*(?:night|nights|n)", text, re.I)
    if m:
        result["nights"] = int(m.group(1))

    # --- Adults ---
    m = re.search(r"(\d+)\s*adults?", text, re.I)
    if m:
        result["adults"] = int(m.group(1))

    # --- Kids ---
    m = re.search(r"(\d+)\s*(?:kids|children|child|infant)", text, re.I)
    if m:
        result["kids"] = int(m.group(1))

    # --- Dates ---
    # DD/MM/YYYY, DD-MM-YYYY, DD Mon YYYY, or just DD Mon
    m = re.search(r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", text)
    if not m:
        m = re.search(r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?(?:\s+\d{2,4})?)", text, re.I)
    if m:
        result["dates"] = m.group(1).strip()

    # --- Budget ---
    m = re.search(r"(?i)(?:budget|₹|rs\.?|inr)\s*\.?\s*(\d[\d,]*)\b", text)
    if m:
        result["budget"] = m.group(1).replace(",", "")

    # --- Occasion ---
    occasion_kw = {
        "honeymoon": "honeymoon",
        "wedding": "wedding",
        "anniversary": "anniversary",
        "birthday": "birthday",
        "family": "family trip",
        "friends": "friends trip",
        "solo": "solo",
        "business": "business",
    }
    for kw, occ in occasion_kw.items():
        if kw in text.lower():
            result["occasion"] = occ
            break

    return result


def format_inquiry_reply(parsed: dict, code: str) -> str:
    """Format a Telegram reply message from parsed inquiry data."""
    lines = [f"✅ Inquiry logged: {code}"]
    if parsed.get("destination"):
        lines.append(f"📍 {parsed['destination']}")
    if parsed.get("nights"):
        lines.append(f"🌙 {parsed['nights']} nights")
    if parsed.get("dates"):
        lines.append(f"📅 {parsed['dates']}")
    if parsed.get("adults") or parsed.get("kids"):
        pax = []
        if parsed.get("adults"):
            pax.append(f"{parsed['adults']} adults")
        if parsed.get("kids"):
            pax.append(f"{parsed['kids']} kids")
        lines.append(f"👥 {', '.join(pax)}")
    if parsed.get("budget"):
        lines.append(f"💰 ₹{parsed['budget']}")
    if parsed.get("occasion"):
        lines.append(f"🎉 {parsed['occasion'].title()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Inquiry code (cached)
# ---------------------------------------------------------------------------

def _cached_or_new_code(session) -> str:
    """Generate an inquiry code with Redis/memory cache (1-hour TTL)."""
    cache_key = f"next_inquiry_code:{datetime.utcnow().date().isoformat()}"
    try:
        from app.cache import get as cache_get, set as cache_set
        cached = cache_get(cache_key)
        if cached:
            return str(cached)
    except Exception:
        pass
    code = next_inquiry_code(session)
    try:
        from app.cache import set as cache_set
        cache_set(cache_key, code, 3600)
    except Exception:
        pass
    return code


# ---------------------------------------------------------------------------
# Dashboard summary engine
# ---------------------------------------------------------------------------

def get_summary(period: str = "today") -> dict:
    """
    Aggregate dashboard stats for a given period.

    Periods: today | month | all
    Returns: {leads, revenue, supplier_out, profit}
    """
    cache_key = f"summary:{period}"
    try:
        from app.cache import get as cache_get, set as cache_set
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
    except Exception:
        pass

    from app.models import Lead, Payment

    today = datetime.utcnow().date()
    q_leads = db.session.query(func.count(Lead.id))
    q_revenue = db.session.query(func.coalesce(func.sum(Payment.amount), 0))
    q_supplier = db.session.query(func.coalesce(func.sum(Payment.amount), 0))

    if period == "today":
        start = datetime(today.year, today.month, today.day)
        end = datetime(today.year, today.month, today.day, 23, 59, 59)
        q_leads = q_leads.filter(Lead.created_at.between(start, end))
        q_revenue = q_revenue.filter(Payment.type == "guest_payment", Payment.paid_at.between(start, end))
        q_supplier = q_supplier.filter(Payment.type == "supplier_payment", Payment.paid_at.between(start, end))
    elif period == "month":
        month_start = datetime(today.year, today.month, 1)
        q_leads = q_leads.filter(Lead.created_at >= month_start)
        q_revenue = q_revenue.filter(Payment.type == "guest_payment", Payment.paid_at >= month_start)
        q_supplier = q_supplier.filter(Payment.type == "supplier_payment", Payment.paid_at >= month_start)
    elif period == "all":
        pass  # no date filter

    revenue = float(q_revenue.scalar() or 0)
    supplier_out = float(q_supplier.scalar() or 0)
    
    # Pipeline stats
    pipeline_new = db.session.query(func.count(Lead.id)).filter(Lead.status == "new").scalar() or 0
    pipeline_progress = db.session.query(func.count(Lead.id)).filter(
        Lead.status.in_(["in_progress", "converted"])).scalar() or 0
    pipeline_done = db.session.query(func.count(Lead.id)).filter(Lead.status == "completed").scalar() or 0
    team_online = db.session.query(func.count(Lead.id)).filter().scalar() or 0  # placeholder
    
    data = {
        "leads": q_leads.scalar() or 0,
        "leads_today": q_leads.scalar() or 0,
        "revenue": revenue,
        "revenue_mtd": revenue,
        "supplier_out": supplier_out,
        "profit": revenue - supplier_out,
        "pipeline_new": pipeline_new,
        "pipeline_progress": pipeline_progress,
        "pipeline_done": pipeline_done,
        "team_online": team_online or "—",
    }

    try:
        from app.cache import set as cache_set
        cache_set(cache_key, data, 60)
    except Exception:
        pass
    return data