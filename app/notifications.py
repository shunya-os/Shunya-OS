"""Shunya OS — Notification Manager.

Cross-channel notifications (in-app, WhatsApp, Telegram, Email).
"""
from typing import Optional
from datetime import datetime
from flask import g, url_for
from app import db
from app.models import Notification, ActivityLog


class NotificationManager:
    """Central notification service."""

    @staticmethod
    def create(tenant_id: int, type: str, title: str, message: str = "",
               user_id: Optional[int] = None, entity_id: Optional[int] = None,
               icon: str = "🔔", link: Optional[str] = None) -> Notification:
        """Create a notification."""
        notif = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            entity_id=entity_id,
            type=type,
            title=title,
            message=message[:500],
            icon=icon,
            link=link,
            is_read=False,
        )
        db.session.add(notif)
        db.session.commit()
        return notif

    @staticmethod
    def get_unread_count(tenant_id: int, user_id: Optional[int] = None) -> int:
        """Count unread notifications for a user."""
        query = Notification.query.filter_by(tenant_id=tenant_id, is_read=False)
        if user_id is not None:
            query = query.filter(
                db.or_(Notification.user_id == user_id, Notification.user_id.is_(None))
            )
        return query.count()

    @staticmethod
    def get_recent(tenant_id: int, user_id: Optional[int] = None, limit: int = 10) -> list:
        """Get recent notifications."""
        query = Notification.query.filter_by(tenant_id=tenant_id)
        if user_id is not None:
            query = query.filter(
                db.or_(Notification.user_id == user_id, Notification.user_id.is_(None))
            )
        notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return [{
            "id": n.id, "type": n.type, "title": n.title, "message": n.message,
            "icon": n.icon, "link": n.link, "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        } for n in notifs]

    @staticmethod
    def mark_read(notification_id: int) -> bool:
        """Mark a notification as read."""
        n = db.session.get(Notification, notification_id)
        if not n:
            return False
        n.is_read = True
        db.session.commit()
        return True

    @staticmethod
    def mark_all_read(tenant_id: int, user_id: Optional[int] = None) -> int:
        """Mark all notifications as read."""
        query = Notification.query.filter_by(tenant_id=tenant_id, is_read=False)
        if user_id is not None:
            query = query.filter(
                db.or_(Notification.user_id == user_id, Notification.user_id.is_(None))
            )
        count = query.count()
        query.update({"is_read": True}, synchronize_session=False)
        db.session.commit()
        return count

    @staticmethod
    def auto_create_from_activity(activity: ActivityLog) -> Optional[Notification]:
        """Auto-create a notification from an ActivityLog entry."""
        type_map = {
            "created": ("entity_created", "New record created"),
            "status_changed": ("status_changed", "Status changed"),
            "updated": ("system", "Record updated"),
            "archived": ("system", "Record archived"),
            "message_sent": ("system", "Message sent"),
        }
        type_info = type_map.get(activity.action)
        if not type_info:
            return None

        return NotificationManager.create(
            tenant_id=activity.tenant_id,
            type=type_info[0],
            title=type_info[1],
            message=activity.detail[:200] if activity.detail else "",
            entity_id=activity.entity_id,
            icon="📋" if activity.action == "created" else "🔄" if activity.action == "status_changed" else "🔔",
            link=f"/entities/{activity.entity_id}" if activity.entity_id else None,
        )