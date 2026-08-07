from app import db
from app.signals.models import Signal


def emit_signal(object_id: int, sig_type: str, payload: dict = None):
    """Emit a signal. No duplicate detection — caller is responsible."""
    signal = Signal(
        object_id=object_id,
        type=sig_type,
        payload=payload or {},
    )
    db.session.add(signal)
    db.session.commit()
    return signal