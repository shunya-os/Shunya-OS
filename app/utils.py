# Shunya OS — Helper utilities
import re, json, hashlib, secrets, uuid
from datetime import datetime, timedelta


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def generate_token(length: int = 64) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def now_utc():
    return datetime.utcnow()


def hours_from_now(hours: int = 24) -> datetime:
    return datetime.utcnow() + timedelta(hours=hours)


def minutes_from_now(minutes: int = 15) -> datetime:
    return datetime.utcnow() + timedelta(minutes=minutes)


def parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
