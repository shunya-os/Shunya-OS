"""Feedback module — user feedback on recommendations.

Phase 5.4: API endpoint POST /api/v1/feedback with fields:
signal_id, accepted (bool), comment (optional).
"""

from .models import Feedback
from .routes import feedback_bp

__all__ = ["Feedback", "feedback_bp"]