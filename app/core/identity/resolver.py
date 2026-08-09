"""Identity Resolution Engine — maps emails, phones, names to Objects.

PHASE 3: Critical for ingesting emails, contacts, and documents.
Without this, every integration creates duplicate entities.

Resolution order:
1. Exact email match (highest priority)
2. Exact phone match
3. Name fuzzy match (lowest priority)
4. Create new Object if not found
"""

import logging
from typing import Optional

from app.core.db import db
from app.core.time import now

logger = logging.getLogger(__name__)


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
            object: The matched or created Object
            matched: True if existing, False if new
            match_field: Which field matched ('email'|'phone'|'name'|'created')
    """
    from app.objects.models import Object

    # 1. Exact email match
    if email:
        email_clean = email.strip().lower()
        existing = Object.query.filter(
            Object.state["email"].astext == email_clean
        ).first()
        if existing:
            logger.info("Identity resolved by email: %s -> Object #%d", email_clean, existing.id)
            return {"object": existing, "matched": True, "match_field": "email"}

    # 2. Exact phone match
    if phone:
        phone_clean = phone.strip()
        existing = Object.query.filter(
            Object.state["phone"].astext == phone_clean
        ).first()
        if existing:
            logger.info("Identity resolved by phone: %s -> Object #%d", phone_clean, existing.id)
            return {"object": existing, "matched": True, "match_field": "phone"}

    # 3. Name match
    if name:
        name_clean = name.strip()
        existing = Object.query.filter(
            Object.state["name"].astext == name_clean
        ).first()
        if existing:
            logger.info("Identity resolved by name: %s -> Object #%d", name_clean, existing.id)
            return {"object": existing, "matched": True, "match_field": "name"}

    # 4. Create new Object
    state = {"name": name or "Unknown", "source": source}
    if email:
        state["email"] = email.strip().lower()
    if phone:
        state["phone"] = phone.strip()
    if metadata:
        state.update(metadata)

    obj = Object(type="person", state=state)
    db.session.add(obj)
    db.session.flush()

    logger.info("Identity created: %s -> Object #%d", name or email or phone, obj.id)
    return {"object": obj, "matched": False, "match_field": "created"}