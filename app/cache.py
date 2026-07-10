"""
Panchi Club — Cache & Async (Unit 6, v2)

Redis cache wrapper with in-memory fallback, batch ops,
and async Celery tasks for PDF generation + activity logging.
"""

import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger("app.cache")

_REDIS_URL = os.getenv("REDIS_URL")
_client = None
_FallbackMap: dict[str, Any] = {}
_CACHE_STATS = {"hits": 0, "misses": 0, "sets": 0}


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import redis as redis_module

        _client = redis_module.from_url(
            _REDIS_URL or "redis://localhost:6379/0",
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        _client.ping()
        logger.info("Redis connected at %s", _REDIS_URL or "localhost")
        return _client
    except Exception as e:
        logger.warning("Redis unavailable, in-memory fallback: %s", e)
        _FallbackMap.clear()
        _client = None
        return None


def get(key: str) -> Optional[Any]:
    client = _get_client()
    if client is not None:
        try:
            raw = client.get(key)
            if raw is None:
                _CACHE_STATS["misses"] += 1
                return None
            _CACHE_STATS["hits"] += 1
            return json.loads(raw)
        except Exception:
            return raw
    _CACHE_STATS["hits" if key in _FallbackMap else "misses"] += 1
    return _FallbackMap.get(key)


def set(key: str, value: Any, ttl: int = 300) -> None:
    client = _get_client()
    if client is not None:
        try:
            raw = json.dumps(value) if not isinstance(value, str) else value
            client.setex(key, ttl, raw)
            _CACHE_STATS["sets"] += 1
            return
        except Exception as e:
            logger.warning("Redis set failed: %s", e)
    _FallbackMap[key] = value
    _CACHE_STATS["sets"] += 1


def delete(key: str) -> None:
    client = _get_client()
    if client is not None:
        try:
            client.delete(key)
            return
        except Exception:
            pass
    _FallbackMap.pop(key, None)


def clear() -> None:
    """Clear in-memory fallback cache."""
    _FallbackMap.clear()


def stats() -> dict:
    """Return cache hit/miss/set statistics."""
    return dict(_CACHE_STATS)


# ---------------------------------------------------------------------------
# Celery async tasks
# ---------------------------------------------------------------------------

celery_app = None


def get_celery():
    """Lazy Celery app init — only loads if REDIS_URL is set."""
    global celery_app
    if celery_app is not None:
        return celery_app
    broker = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL")
    if not broker:
        logger.info("No broker URL — Celery disabled")
        return None
    try:
        from celery import Celery

        celery_app = Celery("panchi", broker=broker, backend=broker)
        celery_app.conf.task_serializer = "json"
        celery_app.conf.result_serializer = "json"
        celery_app.conf.accept_content = ["json"]
        celery_app.conf.task_track_started = True
        _register_tasks(celery_app)
        logger.info("Celery initialised with broker: %s", broker[:30])
        return celery_app
    except Exception as e:
        logger.warning("Celery init failed: %s", e)
        return None


def _register_tasks(app):
    """Define Celery tasks on the app instance."""

    @app.task(bind=True, max_retries=3, default_retry_delay=60)
    def generate_invoice_pdf(self, invoice_id: int):
        """Async PDF generation for an invoice."""
        from app.models import Invoice, Lead
        from app import db
        import pdfkit, os

        inv = db.session.get(Invoice, invoice_id)
        if not inv:
            raise ValueError(f"Invoice {invoice_id} not found")
        lead = inv.lead
        path = os.path.join("invoices", f"{inv.id}_{inv.invoice_number}.pdf")
        os.makedirs("invoices", exist_ok=True)

        due_str = inv.due_date.strftime("%d-%m-%Y") if inv.due_date else ""
        paid_str = inv.paid_at.strftime("%d-%m-%Y") if inv.paid_at else ""
        html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
          body{{font-family:Arial,sans-serif;color:#111;padding:40px}}
          h1{{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px}}
          table{{width:100%;border-collapse:collapse;margin:16px 0}}
          td,th{{border:1px solid #e5e7eb;padding:10px 8px;text-align:left}}
          th{{background:#f9fafb}}
          .footer{{color:#6b7280;font-size:12px;margin-top:32px;text-align:center}}
        </style></head><body>
          <h1>Invoice {inv.invoice_number}</h1>
          <p style="color:#6b7280">Raised: {inv.raised_at.strftime('%d-%m-%Y %H:%M')} · Status: {inv.status}</p>
          <h3>Customer</h3>
          <p>{lead.customer_name if lead else '-'}<br>{lead.email or ''}<br>{lead.phone or ''}</p>
          <h3>Amounts</h3>
          <table>
            <tr><th>Total</th><td>{inv.currency} {inv.total_amount:.2f}</td></tr>
            <tr><th>Tax ({inv.tax_rate:.1f}%)</th><td>{inv.currency} {inv.tax:.2f}</td></tr>
            <tr><th>Discount</th><td>{inv.currency} {inv.discount:.2f}</td></tr>
            <tr><th><strong>Grand Total</strong></th><td><strong>{inv.currency} {inv.grand_total:.2f}</strong></td></tr>
          </table>
          {f'<p>Due: {due_str}</p>' if due_str else ''}
          {f'<p>Paid: {paid_str}</p>' if paid_str else ''}
          <div class="footer">AI@panchi.club · Panchi Club Travel OS</div>
        </body></html>"""
        pdfkit.from_string(html, path)
        inv.pdf_path = path
        db.session.commit()
        return path

    @app.task
    def log_activity_async(lead_id: int, action: str, detail: str, user: str = ""):
        """Async activity logging — non-blocking audit trail."""
        from app.models import ActivityLog
        from app import db

        log = ActivityLog(lead_id=lead_id, action=action, detail=detail[:500], user=user)
        db.session.add(log)
        db.session.commit()
        return log.id


def generate_invoice_pdf_sync(invoice_id: int) -> str:
    """Generate invoice PDF — sync for inline use, async capable if Celery is configured."""
    celery = get_celery()
    if celery:
        task = celery.tasks.get("generate_invoice_pdf")
        if task:
            return task.delay(invoice_id).get(timeout=30)
    # Fallback: run inline
    return _generate_invoice_pdf_inline(invoice_id)


def _generate_invoice_pdf_inline(invoice_id: int) -> str:
    """Inline PDF generation fallback."""
    from app.models import Invoice
    from app import db
    import pdfkit, os

    inv = db.session.get(Invoice, invoice_id)
    if not inv:
        raise ValueError(f"Invoice {invoice_id} not found")
    lead = inv.lead
    path = os.path.join("invoices", f"{inv.id}_{inv.invoice_number}.pdf")
    os.makedirs("invoices", exist_ok=True)

    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
      body{{font-family:Arial,sans-serif;color:#111;padding:40px}}
      h1{{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px}}
      table{{width:100%;border-collapse:collapse;margin:16px 0}}
      td,th{{border:1px solid #e5e7eb;padding:10px 8px}}
      th{{background:#f9fafb}}
    </style></head><body>
      <h1>Invoice {inv.invoice_number}</h1>
      <p style="color:#6b7280">Raised: {inv.raised_at.strftime('%d-%m-%Y %H:%M')} · Status: {inv.status}</p>
      <h3>Customer</h3>
      <p>{lead.customer_name if lead else '-'}<br>{lead.email or ''}<br>{lead.phone or ''}</p>
      <h3>Amounts</h3>
      <table>
        <tr><th>Total</th><td>{inv.currency} {inv.total_amount:.2f}</td></tr>
        <tr><th>Tax</th><td>{inv.currency} {inv.tax:.2f}</td></tr>
        <tr><th>Discount</th><td>{inv.currency} {inv.discount:.2f}</td></tr>
        <tr><th><strong>Grand Total</strong></th><td><strong>{inv.currency} {inv.grand_total:.2f}</strong></td></tr>
      </table>
    </body></html>"""
    pdfkit.from_string(html, path)
    inv.pdf_path = path
    db.session.commit()
    return path