from datetime import datetime, timezone
from app import db
from app.signals.models import Signal

logger = __import__("logging").getLogger(__name__)


def emit_signal(object_id: int, sig_type: str, payload: dict = None,
                *,
                organization_id: int | None = None,
                identity_id: str | None = None):
    """Emit a signal. No duplicate detection — caller is responsible.

    When organization_id and identity_id are provided, automatically creates
    an attention item so the signal→attention bridge is push-based (not
    dependent on the user opening the intention UI).
    """
    signal = Signal(
        object_id=object_id,
        type=sig_type,
        payload=payload or {},
    )
    db.session.add(signal)
    db.session.commit()

    # Push-based attention bridge: if tenant context is provided, immediately
    # create an attention item. This means business state changes produce
    # attention items without the user first opening /api/v1/intention.
    if organization_id and identity_id:
        try:
            from app.attention.service import create_attention_item
            from app.attention.models import AttentionSource

            # Dedup: check if an active attention item already exists
            from sqlalchemy import text
            existing_id = db.session.execute(
                text(
                    "SELECT id FROM attention_items WHERE organization_id = :oid "
                    "AND state = 'active' AND related_object_id = :rid "
                    "AND source = :src LIMIT 1"
                ), {
                    "oid": organization_id,
                    "rid": str(signal.id),
                    "src": AttentionSource.SIGNAL.value,
                }
            ).scalar()

            if not existing_id:
                create_attention_item(
                    identity_id=identity_id,
                    organization_id=organization_id,
                    source=AttentionSource.SIGNAL.value,
                    related_object_type=sig_type,
                    related_object_id=str(signal.id),
                    reason=payload.get("reason", f"Signal detected: {sig_type}"),
                    priority=payload.get("priority", 3),
                    confidence=payload.get("confidence", None),
                    provenance={
                        "detected_at": datetime.now(timezone.utc).isoformat(),
                        "signal_id": signal.id,
                        "method": "emit_signal_push",
                    },
                )
        except Exception as exc:
            logger.warning("Attention item creation from signal %s failed: %s",
                           signal.id, exc)

    return signal