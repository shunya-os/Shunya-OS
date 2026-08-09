"""ACTIVATION-01 API layer — bridge between UI and existing runtime."""

from flask import Blueprint, jsonify, request

activation_bp = Blueprint("activation", __name__, url_prefix="/api/v2")

from app.activation import routes  # noqa: F401 E402