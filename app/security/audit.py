"""SHUNYA OS — Audit Logging (Enterprise CRUD Audit).

Provides an AuditLog model that records every CRUD operation
performed on business objects. This is separate from the
destructive-actions audit log in app.genesis_protection.

Usage:
    from app.security.audit import AuditLog, log_audit

    log_audit("create", "contact", contact_id, details={"name": "..."})
"""

from datetime import datetime

from app import db


class AuditLog(db.Model):
    """Enterprise CRUD audit log — one row per audited operation.

    Tracks who did what, to which resource, from where, and any
    relevant context in the JSON ``details`` column.
    """

    __tablename__ = "sh_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    identity_id = db.Column(db.String(64), default="anonymous")
    workspace_id = db.Column(db.String(20), default="")
    action = db.Column(db.String(50), nullable=False)  # create, read, update, delete
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(50), default="")
    ip_address = db.Column(db.String(50), default="")
    user_agent = db.Column(db.String(500), default="")
    details = db.Column(db.JSON, default=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "identity_id": self.identity_id,
            "workspace_id": self.workspace_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details or {},
        }


def log_audit(
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    """Convenience helper to write an audit log entry.

    Automatically captures the current request context (identity,
    workspace, IP, user-agent) from Flask's ``g`` and ``request``.

    Parameters
    ----------
    action : str
        One of ``create``, ``read``, ``update``, ``delete``.
    resource_type : str
        The type of the resource being acted upon (e.g. ``contact``).
    resource_id : str, optional
        The primary key or logical identifier of the resource.
    details : dict, optional
        Arbitrary JSON-serialisable context.

    Returns
    -------
    AuditLog
        The newly created audit record.
    """
    from flask import g, request

    log = AuditLog(
        identity_id=getattr(g, "identity_id", "anonymous"),
        workspace_id=request.headers.get("X-Workspace-Id", "") if request else "",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id or "",
        ip_address=request.remote_addr or "" if request else "",
        user_agent=str(request.user_agent or "")[:500] if request and request.user_agent else "",
        details=details or {},
    )
    db.session.add(log)
    db.session.commit()
    return log