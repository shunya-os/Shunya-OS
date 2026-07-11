"""
Panchi Club Travel OS — Notification Manager (Unit 8)

Central notification service that creates, retrieves, and manages
in-app notifications. Supports optional user/lead/tenant scoping
and can auto-create notifications from ActivityLog entries.

Usage:
    from app.notifications import NotificationManager
    nm = NotificationManager()
    nm.create_notification(type="lead_created", title="New lead!",
                            user_id=1, lead_id=42)
"""

from datetime import datetime
from typing import Optional
from app import db
from app.models import Notification, NotificationType, ActivityLog


class NotificationManager:
    """Central service for creating and managing notifications."""

    def create_notification(
        self,
        type: str,
        title: str,
        message: str = "",
        user_id: Optional[int] = None,
        lead_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        icon: Optional[str] = None,
        link: Optional[str] = None,
    ) -> Notification:
        """Create a new notification and persist it.

        Args:
            type: One of NotificationType values (lead_created, payment_received, etc.)
            title: Short notification headline
            message: Longer description / body text
            user_id: Target user (None = system-wide)
            lead_id: Related lead (optional)
            tenant_id: Tenant scope (optional)
            icon: Emoji/icon override (defaults based on type)
            link: URL route the notification links to

        Returns:
            The persisted Notification instance.
        """
        # Auto-assign icon based on type if not provided
        if icon is None:
            icon_map = {
                NotificationType.LEAD_CREATED.value: "📋",
                NotificationType.PAYMENT_RECEIVED.value: "💰",
                NotificationType.STATUS_CHANGED.value: "🔄",
                NotificationType.TASK_ASSIGNED.value: "✅",
                NotificationType.CELEBRATION.value: "🎉",
                NotificationType.SYSTEM.value: "🔔",
            }
            icon = icon_map.get(type, "🔔")

        notif = Notification(
            type=type,
            title=title,
            message=message,
            user_id=user_id,
            lead_id=lead_id,
            tenant_id=tenant_id,
            icon=icon,
            link=link,
            is_read=False,
            created_at=datetime.utcnow(),
        )
        db.session.add(notif)
        db.session.commit()
        return notif

    def get_for_user(
        self, user_id: Optional[int] = None, limit: int = 20
    ) -> list[Notification]:
        """Get notifications for a user (or all if user_id is None).

        Returns notifications ordered by created_at descending.
        """
        query = Notification.query
        if user_id is not None:
            query = query.filter(
                (Notification.user_id == user_id) | (Notification.user_id.is_(None))
            )
        return (
            query.order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_unread_count(self, user_id: Optional[int] = None) -> int:
        """Count unread notifications for a user (or overall if None)."""
        query = Notification.query.filter(Notification.is_read == False)
        if user_id is not None:
            query = query.filter(
                (Notification.user_id == user_id) | (Notification.user_id.is_(None))
            )
        return query.count()

    def get_recent_unread(
        self, user_id: Optional[int] = None, limit: int = 10
    ) -> list[Notification]:
        """Get the most recent unread notifications."""
        query = Notification.query.filter(Notification.is_read == False)
        if user_id is not None:
            query = query.filter(
                (Notification.user_id == user_id) | (Notification.user_id.is_(None))
            )
        return (
            query.order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_read(self, notification_id: int) -> bool:
        """Mark a single notification as read. Returns True if found."""
        notif = db.session.get(Notification, notification_id)
        if not notif:
            return False
        notif.is_read = True
        db.session.commit()
        return True

    def mark_all_read(self, user_id: Optional[int] = None) -> int:
        """Mark all notifications as read for a user (or all if None).

        Returns the count of notifications marked.
        """
        query = Notification.query.filter(Notification.is_read == False)
        if user_id is not None:
            query = query.filter(
                (Notification.user_id == user_id) | (Notification.user_id.is_(None))
            )
        count = query.count()
        query.update({"is_read": True}, synchronize_session=False)
        db.session.commit()
        return count

    def create_from_activity_log(
        self, activity: ActivityLog
    ) -> Optional[Notification]:
        """Auto-create a notification from an ActivityLog entry.

        Maps activity actions to notification types and generates
        appropriate titles/messages/icons.

        Args:
            activity: An ActivityLog instance (must be persisted).

        Returns:
            The created Notification, or None if activity is not fresh.
        """
        type_map = {
            "created": NotificationType.LEAD_CREATED.value,
            "payment_received": NotificationType.PAYMENT_RECEIVED.value,
            "status_changed": NotificationType.STATUS_CHANGED.value,
            "task_assigned": NotificationType.TASK_ASSIGNED.value,
            "note_added": NotificationType.SYSTEM.value,
            "proposal_sent": NotificationType.SYSTEM.value,
        }
        title_map = {
            "created": "New Lead Created",
            "payment_received": "Payment Received",
            "status_changed": "Lead Status Changed",
            "task_assigned": "Task Assigned",
            "note_added": "Note Added",
            "proposal_sent": "Proposal Sent",
        }
        icon_map = {
            "created": "📋",
            "payment_received": "💰",
            "status_changed": "🔄",
            "task_assigned": "✅",
            "note_added": "📝",
            "proposal_sent": "📄",
        }

        action = activity.action
        notif_type = type_map.get(action)
        if not notif_type:
            return None

        title = title_map.get(action, "Activity Update")
        icon = icon_map.get(action, "🔔")
        detail = (activity.detail or "")[:200]

        notif = self.create_notification(
            type=notif_type,
            title=title,
            message=detail,
            user_id=None,  # System-wide — visible to all
            lead_id=activity.lead_id,
            icon=icon,
            link=f"/leads/{activity.lead_id}" if activity.lead_id else None,
        )
        return notif

    def auto_create_from_recent_activities(self, limit: int = 50) -> int:
        """Scan recent ActivityLog entries and create notifications for
        any that don't already have a matching notification.

        This can be run as a scheduled task or on demand to backfill
        notifications from the activity trail.

        Returns the number of new notifications created.
        """
        created_count = 0
        activities = (
            ActivityLog.query
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )

        existing_lead_ids = set()
        recent_notifs = (
            Notification.query
            .filter(Notification.lead_id.isnot(None))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        for n in recent_notifs:
            if n.lead_id:
                existing_lead_ids.add((n.lead_id, n.type))

        for activity in activities:
            # Skip if we already have a notification for this lead+type combo
            if activity.lead_id and (activity.lead_id, activity.action) in existing_lead_ids:
                continue
            result = self.create_from_activity_log(activity)
            if result:
                created_count += 1

        return created_count