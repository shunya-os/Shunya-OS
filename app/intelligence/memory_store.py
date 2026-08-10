"""Memory Store — persistent learning weights for the intelligence system.

PHASE 3.4: Stores confidence weights by signal_type and entity_type.
Learning affects future decisions automatically.
"""

import json
import logging
from typing import Any

from app.core.db import get_session, db
from app.core.time import now

logger = logging.getLogger(__name__)


class LearningWeight(db.Model):
    """Persistent learning weight for a signal or entity type."""

    __tablename__ = "learning_weights"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True, index=True)
    weight = db.Column(db.Float, default=0.5)
    sample_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=now)


def get_weight(key: str, default: float = 0.5) -> float:
    """Get the learned weight for a key."""
    try:
        entry = LearningWeight.query.filter_by(key=key).first()
        if entry:
            return entry.weight
    except Exception:
        pass
    return default


def update_weight(key: str, delta: float) -> float:
    """Update the weight for a key by delta.

    Positive delta for success, negative for failure.
    Bounded between 0.15 (entropy floor) and 0.95 (ceiling).
    Decays toward 0.5 over time to prevent oscillation.

    PHASE 3.4: Stability controls:
    - Entropy floor: 0.15 (never collapses to 0)
    - Ceiling: 0.95 (never explodes to 1)
    - Decay: weights drift back to 0.5 over time
    """
    try:
        entry = LearningWeight.query.filter_by(key=key).first()
        if entry:
            # Apply decay toward 0.5 (prevents runaway)
            decay_rate = 0.02
            if entry.weight > 0.5:
                entry.weight -= decay_rate
            elif entry.weight < 0.5:
                entry.weight += decay_rate

            entry.weight = max(0.15, min(0.95, entry.weight + delta))
            entry.sample_count = (entry.sample_count or 0) + 1
            entry.last_updated = now()
            get_session().flush()
            return entry.weight
        else:
            entry = LearningWeight(
                key=key,
                weight=max(0.15, min(0.95, 0.5 + delta)),
                sample_count=1,
            )
            get_session().add(entry)
            get_session().flush()
            return entry.weight
    except Exception as e:
        logger.debug("Could not update weight for %s: %s", key, e)
        return 0.5


def get_all_weights() -> dict:
    """Get all learning weights as a dict."""
    try:
        entries = LearningWeight.query.order_by(LearningWeight.id.desc()).limit(100).all()
        return {
            e.key: {"weight": e.weight, "samples": e.sample_count, "last_updated": e.last_updated.isoformat() if e.last_updated else None}
            for e in entries
        }
    except Exception:
        return {}


def record_success(signal_type: str, entity_type: str):
    """Record a successful execution outcome — boosts confidence."""
    for key in [f"signal:{signal_type}", f"entity:{entity_type}"]:
        new_weight = update_weight(key, 0.05)
        logger.debug("Memory: success for %s -> weight=%.3f", key, new_weight)


def record_failure(signal_type: str, entity_type: str, pattern: str = None):
    """Record a failed execution outcome — reduces confidence."""
    for key in [f"signal:{signal_type}", f"entity:{entity_type}"]:
        new_weight = update_weight(key, -0.1)
        logger.debug("Memory: failure for %s -> weight=%.3f", key, new_weight)
    if pattern:
        update_weight(f"pattern:{pattern}", -0.15)