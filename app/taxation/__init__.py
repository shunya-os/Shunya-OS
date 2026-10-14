"""Taxation rules engine — blueprint registration."""
from flask import Blueprint

taxation_bp = Blueprint("taxation", __name__, url_prefix="/api/v1/taxation")

def register_routes():
    from app.taxation import routes  # noqa

register_routes()