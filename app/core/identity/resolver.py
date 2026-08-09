"""Identity Resolution Engine — maps emails, phones, names to Objects.

PHASE 3: Production-safe identity resolution with normalization,
confidence scoring, and deduplication protection.

Resolution order:
1. Exact email match (highest confidence: 0.95)
2. Exact phone match (confidence: 0.90)
3. Name exact match (confidence: 0.80)
4. Create new Object if not found

Normalization:
- Email: strip, lowercase
- Phone: strip spaces, dashes, dots
"""

import logging
from typing import Optional

from app.core.db import db
from app.core.time import now

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    """Normalize email address: strip whitespace, lowercase."""
    return email.strip().lower()


def normalize_phone(phone: str) -> str:
    """Normalize phone number: remove spaces, dashes, dots."""
    clean = phone.strip()
    for ch in [" ", "-", ".", "(", ")", "+"]:
        clean = clean.replace(ch, "")
    # Ensure leading + is preserved
    if phone.strip().startswith("+") and not clean.startswith("+"):
        clean = "+" + clean
    return clean


def _search_state_field(field_name: str, value: str):
    """Search for a value in Object state JSON field."""
    from app.objects.models import Object
    try:
        return Object.query.filter(
            Object.state[field_name].astext == value
        ).first()
    except Exception:
        # Fallback to full scan for SQLite compatibility
        all_objects = Object.query.all()
        for obj in all_objects:
            state = obj.state or {}
            if state.get(field_name) == value:
                return obj
        return None


def resolve_identity(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    source: str = "integration",
    metadata: Optional[dict] = None,
) -> dict:
    """Resolve an identity to an existing Object or create a new one.

    Args:
        email: Primary identifier (highest priority match).
        phone: Secondary identifier.
        name: Display name / fallback.
        source: Source of the identity (e.g., 'gmail', 'contacts').
        metadata: Optional additional state to store.

    Returns:
        dict with:
            object: The matched or created Object instance
            matched: True if existing, False if new
            confidence: Float 0.0-1.0
            match_field: Which field matched ('email'|'phone'|'name'|'created')
    """
    from app.objects.models import Object

    normalized = {}

    # 1. Exact email match (highest confidence)
    if email:
        normalized["email"] = normalize_email(email)
        existing = _search_state_field("email", normalized["email"])
        if existing:
            logger.info(
                "Identity resolved by email: %s -> Object #%d (confidence=0.95)",
                normalized["email"], existing.id,
            )
            return {
                "object": existing,
                "matched": True,
                "confidence": 0.95,
                "match_field": "email",
            }

    # 2. Exact phone match
    if phone:
        normalized["phone"] = normalize_phone(phone)
        existing = _search_state_field("phone", normalized["phone"])
        if existing:
            logger.info(
                "Identity resolved by phone: %s -> Object #%d (confidence=0.90)",
                normalized["phone"], existing.id,
            )
            return {
                "object": existing,
                "matched": True,
                "confidence": 0.90,
                "match_field": "phone",
            }

    # 3. Name exact match
    if name:
        name_clean = name.strip()
        existing = _search_state_field("name", name_clean)
        if existing:
            logger.info(
                "Identity resolved by name: %s -> Object #%d (confidence=0.80)",
                name_clean, existing.id,
            )
            return {
                "object": existing,
                "matched": True,
                "confidence": 0.80,
                "match_field": "name",
            }

    # 4. Create new Object
    state = {"name": name or "Unknown", "source": source}
    if email:
        state["email"] = normalize_email(email)
    if phone:
        state["phone"] = normalize_phone(phone)
    if metadata:
        state.update(metadata)

    obj = Object(type="person", state=state)
    db.session.add(obj)
    db.session.flush()

    logger.info("Identity created: %s -> Object #%d", name or email or phone, obj.id)
    return {
        "object": obj,
        "matched": False,
        "confidence": 0.50,
        "match_field": "created",
    }