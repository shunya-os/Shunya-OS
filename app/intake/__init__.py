"""Intake — Universal translation layer. Unstructured → Structured."""
from .models import IntakeSignal
from .service import IntakeService
from .routes import intake_bp

__all__ = ["IntakeSignal", "IntakeService", "intake_bp"]