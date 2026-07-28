"""SHUNYA — Founder Experience (Sprint 1).

The complete first Founder Journey.
Uses only frozen kernel primitives. No new architecture.

Routes at /founder/* (HTML pages) and /api/v1/founder/* (JSON API).
"""
from flask import Blueprint

founder_bp = Blueprint("founder", __name__, template_folder="templates/founder")

from app.founder.routes import *  # noqa: F401, E402

__all__ = ["founder_bp"]
