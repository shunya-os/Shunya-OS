"""
SHUNYA OS — Payment Gateway (Stub — no fake payment processing).

THIS IS A STUB. It does NOT process payments and never will: the no-fake rule
requires that a payment is only ever marked "paid" from a REAL provider
transaction reference (e.g. a Razorpay ``pay_...`` payment id received through
the signed webhook at POST /api/v1/payments/razorpay/webhook, which records a
FinancePayment row keyed by that real id).

  - create_payment_link() — records a payment *request* only. The record is
    persisted in the ``gateway_payments`` table so state survives restarts.
    It charges nobody.
  - verify_payment()      — REFUSES to fabricate success. Returns verified=True
    only when a REAL provider transaction reference is supplied AND a
    persisted FinancePayment row (written by the webhook) confirms capture —
    or the Razorpay API itself confirms the payment is captured. Fabricated /
    unknown ids return an honest unverified error.
  - process_refund()      — refuses (there is no real capture to refund).
  - generate_receipt()    — informational only; never claims a payment is real
    unless verified against a real provider transaction.

Until a real provider flow is connected, all payment capture happens through
the Razorpay webhook in app/razorpay/routes.py.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory payment store (simulates a payment provider's DB)
# ---------------------------------------------------------------------------
_payment_store: dict[str, dict] = {}
_refund_store: dict[str, dict] = {}


def _generate_payment_id() -> str:
    return f"pay_{uuid.uuid4().hex[:16]}"


def _generate_transaction_id() -> str:
    return f"txn_{uuid.uuid4().hex[:12].upper()}"


def _generate_refund_id() -> str:
    return f"ref_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# PaymentGateway
# ---------------------------------------------------------------------------

class PaymentGateway:
    """
    Payment gateway STUB — drop-in replacement point for Razorpay / Stripe.

    No method here ever fabricates a successful payment. When a real provider
    is connected:
        - create_payment_link  →  razorpay.payment_link.create(...)
        - verify_payment       →  razorpay.payment.fetch(...) / persisted webhook rows
        - process_refund       →  razorpay.payment.refund(...)

    All methods accept and return plain dicts for maximum compatibility.
    """

    PROVIDER = "stub"  # Real provider id once connected (e.g. "razorpay")
    CURRENCIES = ("INR", "USD", "EUR", "GBP")

    # ------------------------------------------------------------------
    # Persistence — payment request state survives restarts
    # ------------------------------------------------------------------
    @staticmethod
    def _ensure_store_table():
        """Create the gateway_payments table if it doesn't exist."""
        from app import db
        from sqlalchemy import text
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS gateway_payments (
                payment_id VARCHAR(64) PRIMARY KEY,
                lead_id INTEGER,
                amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
                currency VARCHAR(10) DEFAULT 'INR',
                description TEXT DEFAULT '',
                status VARCHAR(30) DEFAULT 'created',
                transaction_reference VARCHAR(255) DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW(),
                paid_at TIMESTAMP
            )
        """))
        db.session.commit()

    @staticmethod
    def _persist_request(record: dict) -> None:
        """Best-effort persistence of a payment *request* (charges nobody)."""
        try:
            from app import db
            from sqlalchemy import text
            PaymentGateway._ensure_store_table()
            db.session.execute(text("""
                INSERT INTO gateway_payments
                    (payment_id, lead_id, amount, currency, description, status,
                     transaction_reference, created_at)
                VALUES (:pid, :lead_id, :amount, :currency, :description,
                        :status, :txn, :created_at)
                ON CONFLICT (payment_id) DO NOTHING
            """), {
                "pid": record["payment_id"],
                "lead_id": record.get("lead_id"),
                "amount": record.get("amount", 0),
                "currency": record.get("currency", "INR"),
                "description": record.get("description", ""),
                "status": record.get("status", "created"),
                "txn": record.get("transaction_reference") or "",
                "created_at": record.get("created_at"),
            })
            db.session.commit()
        except Exception:
            logger.exception(
                "PaymentGateway: failed to persist payment request %s "
                "(in-memory copy remains)", record.get("payment_id"),
            )
            from app import db as _db
            try:
                _db.session.rollback()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Create a payment link (a *request*, never a charge)
    # ------------------------------------------------------------------
    def create_payment_link(
        self,
        lead_id: int,
        amount: float,
        description: str,
        currency: str = "INR",
    ) -> dict:
        """
        Record a payment link REQUEST (stub — no money moves).

        The record is persisted (``gateway_payments`` table, survives
        restart) with status ``created``. Nothing here marks it paid; only a
        real provider transaction (Razorpay webhook) can do that.

        Returns:
            {
                "payment_url":   str  — URL for the (legacy) checkout page
                "payment_id":    str  — local request id
                "amount":        float
                "currency":      str
                "description":   str
                "lead_id":       int
                "status":        str  — "created"
                "created_at":    str  — ISO datetime
            }
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        if currency not in self.CURRENCIES:
            raise ValueError(f"Unsupported currency '{currency}'. Choose from: {', '.join(self.CURRENCIES)}")

        payment_id = _generate_payment_id()
        record = {
            "payment_url": f"/payment/checkout/{payment_id}",
            "payment_id": payment_id,
            "amount": round(amount, 2),
            "currency": currency.upper(),
            "description": description,
            "lead_id": lead_id,
            "status": "created",
            "verified": False,
            "transaction_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "paid_at": None,
        }
        _payment_store[payment_id] = record
        self._persist_request(record)
        return {
            "payment_url": record["payment_url"],
            "payment_id": record["payment_id"],
            "amount": record["amount"],
            "currency": record["currency"],
            "description": record["description"],
            "lead_id": record["lead_id"],
            "status": record["status"],
            "created_at": record["created_at"],
        }

    # ------------------------------------------------------------------
    # Verify a payment — REAL provider evidence only
    # ------------------------------------------------------------------
    def verify_payment(
        self,
        payment_id: str,
        *,
        organization_id: Optional[int] = None,
        identity_id: Optional[str] = None,
    ) -> dict:
        """
        Verify a payment against REAL provider evidence. Never fabricates.

        Returns verified=True ONLY when:
          1. a persisted FinancePayment row exists with
             reference_number == payment_id (written by the Razorpay webhook
             from a real captured transaction), or
          2. the Razorpay API confirms the payment is captured (keys must be
             resolvable — pass identity_id or have keys saved).

        Any other id (fabricated, unknown, local stub) returns an honest
        ``verified: False`` with a clear error. Callers MUST pass
        ``organization_id`` for the persisted lookup.
        """
        if not payment_id:
            return self._unverified(
                payment_id, "payment_id is required", status="invalid"
            )

        # 1. Persisted truth (written by the real webhook — survives restart)
        if organization_id:
            try:
                from app.finance.models import FinancePayment
                row = FinancePayment.query.filter_by(
                    organization_id=organization_id,
                    reference_number=payment_id,
                ).first()
            except Exception:
                row = None
            if row:
                paid = row.status in ("confirmed", "allocated", "reconciled", "paid")
                return {
                    "verified": paid,
                    "amount": float(row.amount or 0),
                    "transaction_id": payment_id,
                    "status": row.status or ("paid" if paid else "unverified"),
                    "payment_id": payment_id,
                    "currency": row.currency or "INR",
                    "paid_at": row.payment_date.isoformat() if row.payment_date else None,
                    "source": "persisted_webhook",
                }

        # 2. Stub requests are requests — never auto-'paid'.
        record = _payment_store.get(payment_id)
        if record:
            return self._unverified(
                payment_id,
                "This gateway is a stub: no real provider transaction exists for "
                "this payment request. A payment is marked paid only from a real "
                "provider webhook (Razorpay payment_id).",
                status=record.get("status", "created"),
                amount=float(record.get("amount", 0) or 0),
                currency=record.get("currency", "INR"),
            )

        # 3. Real provider check — only when keys are resolvable.
        try:
            from app.razorpay.routes import _get_saved_keys
            keys = _get_saved_keys(identity_id) if identity_id else None
            if keys and str(payment_id).startswith("pay_"):
                import razorpay
                client = razorpay.Client(auth=(keys["key_id"], keys["key_secret"]))
                pay = client.payment.fetch(payment_id)
                captured = (pay or {}).get("status") == "captured"
                return {
                    "verified": captured,
                    "amount": float((pay or {}).get("amount", 0) or 0) / 100,
                    "transaction_id": payment_id,
                    "status": (pay or {}).get("status", "unknown"),
                    "payment_id": payment_id,
                    "currency": (pay or {}).get("currency", "INR"),
                    "paid_at": None,
                }
        except ImportError:
            pass  # razorpay SDK not installed — fall through to honest refusal
        except Exception as e:
            # Provider/network errors are HONEST failures, never success.
            logger.warning("verify_payment: provider check failed for %s: %s", payment_id, e)
            return self._unverified(
                payment_id, f"Provider verification failed: {e}", status="provider_error"
            )

        return self._unverified(
            payment_id,
            f"No real provider transaction reference matches '{payment_id}'. "
            "Supply a real Razorpay payment id (pay_...) recorded by the webhook.",
        )

    @staticmethod
    def _unverified(payment_id, error, status="not_found", amount=0, currency="INR"):
        return {
            "verified": False,
            "amount": amount,
            "transaction_id": None,
            "status": status,
            "payment_id": payment_id,
            "currency": currency,
            "paid_at": None,
            "error": error,
        }

    # ------------------------------------------------------------------
    # Process a refund — refused (no real capture to refund)
    # ------------------------------------------------------------------
    def process_refund(self, payment_id: str, amount: Optional[float] = None) -> dict:
        """
        Refuse refunds: there is no real provider capture to refund (stub).

        Returns an honest ``success: False`` — never a fabricated refund.
        """
        return {
            "success": False,
            "refund_id": None,
            "amount": amount or 0,
            "payment_id": payment_id,
            "status": "refund_unavailable_stub",
            "error": "This gateway is a stub — no real provider capture exists to "
                     "refund. Connect a real provider (Razorpay) to process refunds.",
        }

    # ------------------------------------------------------------------
    # Generate HTML receipt
    # ------------------------------------------------------------------
    def generate_receipt(self, payment_id: str) -> str:
        """
        Generate an HTML receipt string for a completed payment.
        """
        record = _payment_store.get(payment_id)
        if not record:
            return "<h2>Receipt not found</h2><p>No payment record exists for this ID.</p>"

        paid_at_display = ""
        if record.get("paid_at"):
            try:
                dt = datetime.fromisoformat(record["paid_at"])
                paid_at_display = dt.strftime("%d %B %Y, %I:%M %p")
            except (ValueError, TypeError):
                paid_at_display = record["paid_at"]

        created_at_display = ""
        if record.get("created_at"):
            try:
                dt = datetime.fromisoformat(record["created_at"])
                created_at_display = dt.strftime("%d %B %Y, %I:%M %p")
            except (ValueError, TypeError):
                created_at_display = record["created_at"]

        status_display = record.get("status", "unknown").upper()
        status_color = "#059669" if record.get("verified") else "#d97706"

        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Payment Receipt — SHUNYA OS</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f1f5f9;
      color: #0f172a;
      padding: 40px 20px;
      -webkit-font-smoothing: antialiased;
    }}
    .receipt {{
      max-width: 520px;
      margin: 0 auto;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
      overflow: hidden;
    }}
    .receipt-header {{
      background: linear-gradient(135deg, #1e293b, #334155);
      color: #fff;
      padding: 32px 32px 24px;
      text-align: center;
    }}
    .receipt-header .logo {{
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }}
    .receipt-header .logo span {{
      color: #60a5fa;
    }}
    .receipt-header .subtitle {{
      font-size: 12px;
      color: #94a3b8;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .receipt-body {{
      padding: 32px;
    }}
    .status-badge {{
      display: inline-block;
      padding: 6px 16px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #fff;
      background: {status_color};
    }}
    .receipt-row {{
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid #e2e8f0;
      font-size: 14px;
    }}
    .receipt-row:last-child {{
      border-bottom: none;
    }}
    .receipt-row .label {{
      color: #64748b;
    }}
    .receipt-row .value {{
      font-weight: 600;
      color: #0f172a;
      text-align: right;
    }}
    .receipt-row .value.mono {{
      font-family: 'JetBrains Mono', 'SF Mono', monospace;
      font-size: 13px;
    }}
    .amount-large {{
      font-size: 32px;
      font-weight: 700;
      color: #0f172a;
      text-align: center;
      padding: 16px 0 8px;
    }}
    .amount-large .currency {{
      font-size: 18px;
      color: #64748b;
    }}
    .receipt-footer {{
      background: #f8fafc;
      padding: 20px 32px;
      text-align: center;
      font-size: 11px;
      color: #94a3b8;
      border-top: 1px solid #e2e8f0;
    }}
    .receipt-footer strong {{
      color: #475569;
    }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .receipt {{ box-shadow: none; border: 1px solid #e2e8f0; }}
      .no-print {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <div class="receipt">
    <div class="receipt-header">
      <div class="logo">🏝️ <span>SHUNYA</span> OS</div>
      <div class="subtitle">Payment Receipt</div>
    </div>
    <div class="receipt-body">
      <div style="text-align:center;margin-bottom:16px;">
        <span class="status-badge">{status_display}</span>
      </div>
      <div class="amount-large">
        <span class="currency">{record.get('currency', 'INR')}</span> {record.get('amount', 0):,.2f}
      </div>
      <div class="receipt-row">
        <span class="label">Transaction ID</span>
        <span class="value mono">{record.get('transaction_id') or '—'}</span>
      </div>
      <div class="receipt-row">
        <span class="label">Payment ID</span>
        <span class="value mono">{payment_id}</span>
      </div>
      <div class="receipt-row">
        <span class="label">Description</span>
        <span class="value">{record.get('description', '—')}</span>
      </div>
      <div class="receipt-row">
        <span class="label">Lead ID</span>
        <span class="value mono">#{record.get('lead_id', '—')}</span>
      </div>
      <div class="receipt-row">
        <span class="label">Created</span>
        <span class="value">{created_at_display}</span>
      </div>
      <div class="receipt-row">
        <span class="label">Paid At</span>
        <span class="value">{paid_at_display}</span>
      </div>
    </div>
    <div class="receipt-footer">
      <strong>SHUNYA OS</strong> &mdash; Informational Receipt<br>
      This gateway is a stub. A payment is confirmed only via a real provider
      transaction (Razorpay webhook) — nothing here proves money moved.
    </div>
  </div>
</body>
</html>"""
        return html

    # ------------------------------------------------------------------
    # Utility: get payment details
    # ------------------------------------------------------------------
    def get_payment(self, payment_id: str) -> Optional[dict]:
        """Return the raw payment record, or None."""
        return _payment_store.get(payment_id)

    def list_payments(self) -> list[dict]:
        """Return all payment records (for admin/debug)."""
        return list(_payment_store.values())

    def clear_store(self):
        """Clear all payment records (test helper)."""
        _payment_store.clear()
        _refund_store.clear()