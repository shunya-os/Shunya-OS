"""SHUNYA — Communication Intelligence (Production).

AI-powered communication drafting endpoints:
  /draft/email     — Draft an email from intent
  /draft/whatsapp  — Draft a WhatsApp message from intent
  /draft/sms       — Draft an SMS from intent
"""
from flask import Blueprint

communication_bp = Blueprint("communication", __name__, url_prefix="/communication")

# Import route modules — each registers handlers on communication_bp
from app.production.communication.draft_routes import *  # noqa: F401, E402

__all__ = ["communication_bp"]