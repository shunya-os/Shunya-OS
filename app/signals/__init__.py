"""Signal System — generic, system-level signal detection and emission."""
from .models import Signal
from .service import emit_signal

__all__ = ["Signal", "emit_signal"]