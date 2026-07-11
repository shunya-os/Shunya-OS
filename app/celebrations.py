"""
Panchi Club — Celebration Engine (Phase 3H)

Auto-detects wins and celebrations across the platform.
Scans for new leads, conversions, payments, and completed tasks.
Integrates with CompanionEngine for celebration messages.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

from app import db
from app.models import Celebration, Lead, Payment, Task, LeadStatus, PaymentType


class CelebrationEngine:
    """Detects wins, records celebrations, and retrieves recent wins."""

    # Icon/Animation mapping per celebration type
    CELEBRATION_STYLES = {
        "new_lead": {"icon": "🎉", "animation": "woosh", "title_prefix": "New Lead!"},
        "converted": {"icon": "🏆", "animation": "confetti", "title_prefix": "Lead Converted!"},
        "payment": {"icon": "💰", "animation": "confetti", "title_prefix": "Payment Received!"},
        "task_completed": {"icon": "✅", "animation": "woosh", "title_prefix": "Task Completed!"},
        "milestone": {"icon": "🔥", "animation": "confetti", "title_prefix": "Milestone Reached!"},
        "manual": {"icon": "🎉", "animation": "woosh", "title_prefix": "Celebration!"},
        "generic": {"icon": "🎉", "animation": "woosh", "title_prefix": "Win!"},
    }

    # Companion-style celebration message templates
    MESSAGE_TEMPLATES = {
        "new_lead": [
            "{name} just landed — fresh opportunity! 🚀",
            "New inquiry from {name}. Let's go get 'em! 🔥",
            "{name} is in the house! Time to work some magic.",
            "Fresh lead alert: {name} wants to travel! ✈️",
        ],
        "converted": [
            "{name} is officially on the road! 🏆",
            "Booking confirmed for {name}! Another happy traveler!",
            "{name} said YES! Trip locked in! 🎯",
            "Conversion complete for {name}! Crushing it! 🔥",
        ],
        "payment": [
            "₹{amount} received from {name}! 💰",
            "Payment of ₹{amount} cleared for {name}! 🎉",
            "{name} paid ₹{amount} — money in the bank! 💸",
            "₹{amount} in from {name}! Keep the momentum going! 🚀",
        ],
        "task_completed": [
            "✅ {name} checked off! One less thing to worry about.",
            "{name} — done and dusted! Good work team! 🙌",
            "Task complete: {name}! Efficiency level: 100 🔥",
        ],
        "milestone": [
            "🔥 BOOM! {name}! You're on fire today!",
            "Milestone unlocked: {name}! Absolutely crushing it! 🏆",
            "{name} — that's championship behavior right there! 🥇",
        ],
    }

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect_wins(self) -> list[dict]:
        """
        Scan the platform for recent wins and celebrations.
        Checks: new leads (last hour), conversions (today), payments (today), tasks completed (today).
        Returns list of celebration dicts with type, title, message, icon, animation, lead_id, user.
        Does NOT auto-record; returns detected wins for the caller to decide.
        """
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        wins = []

        # 1. New leads in the last hour
        new_leads = (
            Lead.query
            .filter(Lead.created_at >= one_hour_ago)
            .order_by(Lead.created_at.desc())
            .all()
        )
        for lead in new_leads:
            name = lead.customer_name or lead.code
            style = self.CELEBRATION_STYLES["new_lead"]
            message = random.choice(self.MESSAGE_TEMPLATES["new_lead"]).format(name=name)
            wins.append({
                "type": "new_lead",
                "title": f"{style['title_prefix']} {name}",
                "message": message,
                "icon": style["icon"],
                "animation": style["animation"],
                "lead_id": lead.id,
                "user": lead.assigned_to or "",
            })

        # 2. Leads converted today
        converted_leads = (
            Lead.query
            .filter(
                Lead.status == LeadStatus.CONVERTED.value,
                Lead.updated_at >= today_start,
            )
            .order_by(Lead.updated_at.desc())
            .all()
        )
        for lead in converted_leads:
            name = lead.customer_name or lead.code
            style = self.CELEBRATION_STYLES["converted"]
            message = random.choice(self.MESSAGE_TEMPLATES["converted"]).format(name=name)
            wins.append({
                "type": "converted",
                "title": f"{style['title_prefix']} {name}",
                "message": message,
                "icon": style["icon"],
                "animation": style["animation"],
                "lead_id": lead.id,
                "user": lead.assigned_to or "",
            })

        # 3. Payments received today (guest payments)
        payments_today = (
            Payment.query
            .filter(
                Payment.type == PaymentType.GUEST.value,
                Payment.paid_at >= today_start,
            )
            .order_by(Payment.paid_at.desc())
            .all()
        )
        for payment in payments_today:
            lead = payment.lead
            name = lead.customer_name or lead.code if lead else f"Lead #{payment.lead_id}"
            style = self.CELEBRATION_STYLES["payment"]
            amount = f"{float(payment.amount):,.0f}"
            message = random.choice(self.MESSAGE_TEMPLATES["payment"]).format(name=name, amount=amount)
            wins.append({
                "type": "payment",
                "title": f"{style['title_prefix']} ₹{amount}",
                "message": message,
                "icon": style["icon"],
                "animation": style["animation"],
                "lead_id": payment.lead_id,
                "user": lead.assigned_to if lead else "",
            })

        # 4. Tasks completed today
        tasks_done = (
            Task.query
            .filter(
                Task.status == "completed",
                Task.completed_at >= today_start,
            )
            .order_by(Task.completed_at.desc())
            .all()
        )
        for task in tasks_done:
            name = task.title
            style = self.CELEBRATION_STYLES["task_completed"]
            message = random.choice(self.MESSAGE_TEMPLATES["task_completed"]).format(name=name)
            wins.append({
                "type": "task_completed",
                "title": f"✅ {name}",
                "message": message,
                "icon": style["icon"],
                "animation": style["animation"],
                "lead_id": task.task_list.lead_id if task.task_list else None,
                "user": task.assigned_to or "",
            })

        return wins

    # ------------------------------------------------------------------
    # Recording & Retrieval
    # ------------------------------------------------------------------

    def record_celebration(
        self,
        celebration_type: str,
        title: str,
        message: str,
        icon: str = "🎉",
        animation: str = "woosh",
        lead_id: Optional[int] = None,
        created_by: str = "",
    ) -> dict:
        """Record a celebration in the database and return its dict."""
        c = Celebration(
            type=celebration_type,
            title=title,
            message=message,
            icon=icon,
            animation=animation,
            lead_id=lead_id,
            created_by=created_by,
        )
        db.session.add(c)
        db.session.commit()
        return c.to_dict()

    def get_recent_celebrations(self, limit: int = 10) -> list[dict]:
        """Return the most recent celebrations."""
        celebrations = (
            Celebration.query
            .order_by(Celebration.created_at.desc())
            .limit(limit)
            .all()
        )
        return [c.to_dict() for c in celebrations]

    def get_celebration_count_since(self, since: Optional[datetime] = None) -> int:
        """Count celebrations since a given time (default: today at midnight)."""
        if since is None:
            since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return Celebration.query.filter(Celebration.created_at >= since).count()

    # ------------------------------------------------------------------
    # Auto-scan: detect + record new wins
    # ------------------------------------------------------------------

    def scan_and_record(self) -> list[dict]:
        """
        Detect new wins and record any that haven't been recorded yet.
        Uses a simple dedup check by type + lead_id within the last hour.
        Returns list of newly recorded celebrations.
        """
        detected = self.detect_wins()
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        recorded = []

        for win in detected:
            # Dedup: check if a celebration of same type+lead_id exists in last hour
            existing = (
                Celebration.query
                .filter(
                    Celebration.type == win["type"],
                    Celebration.lead_id == win["lead_id"],
                    Celebration.created_at >= one_hour_ago,
                )
                .first()
            )
            if existing:
                continue

            # Record it
            celeb = self.record_celebration(
                celebration_type=win["type"],
                title=win["title"],
                message=win["message"],
                icon=win["icon"],
                animation=win.get("animation", "woosh"),
                lead_id=win["lead_id"],
                created_by=win.get("user", ""),
            )
            recorded.append(celeb)

        return recorded

    # ------------------------------------------------------------------
    # One-shot celebration helpers
    # ------------------------------------------------------------------

    def celebrate_lead_conversion(self, lead_id: int, user: str = "") -> Optional[dict]:
        """Celebrate a lead that was just converted to booked status."""
        lead = db.session.get(Lead, lead_id)
        if not lead:
            return None
        name = lead.customer_name or lead.code
        style = self.CELEBRATION_STYLES["converted"]
        message = random.choice(self.MESSAGE_TEMPLATES["converted"]).format(name=name)
        return self.record_celebration(
            celebration_type="converted",
            title=f"{style['title_prefix']} {name}",
            message=message,
            icon=style["icon"],
            animation=style["animation"],
            lead_id=lead_id,
            created_by=user,
        )

    def celebrate_payment(self, lead_id: int, amount: float, user: str = "") -> Optional[dict]:
        """Celebrate a payment received."""
        lead = db.session.get(Lead, lead_id) if lead_id else None
        name = lead.customer_name or lead.code if lead else "Unknown"
        style = self.CELEBRATION_STYLES["payment"]
        amount_str = f"{float(amount):,.0f}"
        message = random.choice(self.MESSAGE_TEMPLATES["payment"]).format(name=name, amount=amount_str)
        return self.record_celebration(
            celebration_type="payment",
            title=f"{style['title_prefix']} ₹{amount_str}",
            message=message,
            icon=style["icon"],
            animation=style["animation"],
            lead_id=lead_id,
            created_by=user,
        )