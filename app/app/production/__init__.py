"""SHUNYA — Production Services (Milestone X).

Production-grade operational services for SHUNYA:
  identity    — Organizations, workspaces, users, teams, invitations
  auth        — Authentication, MFA, session management, password reset
  events      — SSE event delivery for live runtime
  ops         — Background workers, job queues, scheduled tasks
  observability — Metrics, health, tracing, error reporting
  security    — CSRF, validation, secrets, encryption, audit logging
  performance — Caching, query optimization, profiling
  reliability — Circuit breakers, recovery, backup/restore
"""

from flask import Blueprint

production_bp = Blueprint("production", __name__, url_prefix="/api/v1")

# Import sub-blueprints — each module registers itself on production_bp
from app.production.identity import identity_bp

production_bp.register_blueprint(identity_bp)

__all__ = ["production_bp"]