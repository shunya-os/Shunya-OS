"""Workspace Experience Framework — Blueprint registration."""
from flask import Blueprint

workspace_bp = Blueprint("workspace_exp", __name__)


def register_routes():
    from app.workspace import routes  # noqa: F401


register_routes()