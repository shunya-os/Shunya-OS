"""SHUNYA — Sales Pipeline API (Production).

Proposal and quotation management endpoints.
"""
from flask import Blueprint

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")

from app.production.sales.proposal_routes import sales_proposal_bp  # noqa: E402, F401

sales_bp.register_blueprint(sales_proposal_bp)

__all__ = ["sales_bp"]