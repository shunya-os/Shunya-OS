"""SHUNYA — Finance API (Production).

Invoice and payment management endpoints.
"""
from flask import Blueprint

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

from app.production.finance.invoice_routes import finance_invoice_bp  # noqa: E402, F401
from app.production.finance.payment_routes import finance_payment_bp  # noqa: E402, F401
from app.production.finance.ledger_routes import finance_ledger_bp  # noqa: E402, F401

finance_bp.register_blueprint(finance_invoice_bp)
finance_bp.register_blueprint(finance_payment_bp)
finance_bp.register_blueprint(finance_ledger_bp)

__all__ = ["finance_bp"]