"""
Panchi Club Travel OS — Payment Gateway (Simulated)

Simulated Razorpay/Stripe integration with in-memory payment store.
Designed so switching to a real provider only requires replacing
the mock store with API calls — the interface stays the same.
"""

import uuid
import random
from datetime import datetime
from typing import Optional


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
    Simulated payment gateway — drop-in for real Razorpay / Stripe integration.

    In production, replace the in-memory store methods with REST API calls:
        - create_payment_link  →  razorpay.payment_link.create(...)
        - verify_payment       →  razorpay.payment.fetch(...)
        - process_refund       →  razorpay.payment.refund(...)

    All methods accept and return plain dicts for maximum compatibility.
    """

    PROVIDER = "simulated"  # Override this when integrating a real provider
    CURRENCIES = ("INR", "USD", "EUR", "GBP")

    # ------------------------------------------------------------------
    # Create a payment link
    # ------------------------------------------------------------------
    def create_payment_link(
        self,
        lead_id: int,
        amount: float,
        description: str,
        currency: str = "INR",
    ) -> dict:
        """
        Generate a payment link (simulated). In production this would
        call Razorpay's /payment_links/ endpoint and return a hosted URL.

        Returns:
            {
                "payment_url":   str  — URL for the checkout page
                "payment_id":    str  — unique gateway payment ID
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
            "created_at": datetime.utcnow().isoformat(),
            "paid_at": None,
        }
        _payment_store[payment_id] = record
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
    # Verify a payment
    # ------------------------------------------------------------------
    def verify_payment(self, payment_id: str) -> dict:
        """
        Verify a payment's status. The simulated version "processes" the
        payment on first verification call.

        Returns:
            {
                "verified":        bool
                "amount":          float
                "transaction_id":  str
                "status":          str
                "payment_id":      str
                "currency":        str
                "paid_at":         str | None
            }
        """
        record = _payment_store.get(payment_id)
        if not record:
            return {
                "verified": False,
                "amount": 0,
                "transaction_id": None,
                "status": "not_found",
                "payment_id": payment_id,
                "currency": "INR",
                "paid_at": None,
            }

        # First call — simulate payment processing
        if record["status"] == "created":
            record["status"] = "paid"
            record["verified"] = True
            record["transaction_id"] = _generate_transaction_id()
            record["paid_at"] = datetime.utcnow().isoformat()

        return {
            "verified": record["verified"],
            "amount": record["amount"],
            "transaction_id": record["transaction_id"],
            "status": record["status"],
            "payment_id": record["payment_id"],
            "currency": record["currency"],
            "paid_at": record["paid_at"],
        }

    # ------------------------------------------------------------------
    # Process a refund
    # ------------------------------------------------------------------
    def process_refund(self, payment_id: str, amount: Optional[float] = None) -> dict:
        """
        Process a refund for the given payment.

        Args:
            payment_id:  The gateway payment ID to refund.
            amount:      Optional partial refund amount. Full refund if omitted.

        Returns:
            {
                "success":       bool
                "refund_id":     str
                "amount":        float
                "payment_id":    str
                "status":        str
            }
        """
        record = _payment_store.get(payment_id)
        if not record:
            return {
                "success": False,
                "refund_id": None,
                "amount": 0,
                "payment_id": payment_id,
                "status": "payment_not_found",
            }

        if record["status"] != "paid":
            return {
                "success": False,
                "refund_id": None,
                "amount": 0,
                "payment_id": payment_id,
                "status": "cannot_refund_unpaid",
            }

        refund_amount = amount if amount is not None else record["amount"]
        if refund_amount > record["amount"]:
            return {
                "success": False,
                "refund_id": None,
                "amount": refund_amount,
                "payment_id": payment_id,
                "status": "refund_exceeds_amount",
            }

        refund_id = _generate_refund_id()
        refund_record = {
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": round(refund_amount, 2),
            "status": "processed",
            "created_at": datetime.utcnow().isoformat(),
        }
        _refund_store[refund_id] = refund_record

        return {
            "success": True,
            "refund_id": refund_id,
            "amount": refund_record["amount"],
            "payment_id": payment_id,
            "status": "refund_processed",
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
  <title>Payment Receipt — Panchi Club</title>
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
      <div class="logo">🏝️ <span>Panchi</span> Club</div>
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
      <strong>Panchi Club Travel OS</strong> &mdash; Internal Payment Receipt<br>
      This is a simulated receipt. No real payment has been processed.
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