"""SHUNYA — Objects API (Customer, Supplier, and generic object endpoints).

Object creation and management routes mounted at /api/v1/objects.
"""
from flask import Blueprint

objects_bp = Blueprint("objects", __name__, url_prefix="/objects")

# Import route modules — each registers handlers on objects_bp
from app.production.objects.customer_routes import *  # noqa: F401, E402
from app.production.objects.supplier_routes import *  # noqa: F401, E402
from app.production.objects.itinerary_routes import *  # noqa: F401, E402
from app.production.objects.employee_routes import *  # noqa: F401, E402
from app.production.objects.proposal_routes import *  # noqa: F401, E402

__all__ = ["objects_bp"]