"""Shunya OS — User Intelligence Engine.

Tracks and analyzes user interactions, mood, relationship building,
and work patterns. Provides insights for Bird AI and dashboards.
"""
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy import func, and_, or_

from app import db
from app.models import UserActivityLog, UserDailySummary, UserMoodCheckin

logger = logging.getLogger("shunya.user_intelligence")


class UserIntelligence:
    """Analyzes user behavior patterns on the platform."""

    @staticmethod
    def log_activity(
        tenant_id: int,
        user_id: int,
        activity_type: str,
        page_path: str = "",
        page_title: str = "",
        session_id: str = "",
        duration: int = 0,
        metadata: Optional[dict] = None,
        device_info: str = "",
        ip_address: str = "",
    ) -> dict:
        """Log a user activity record."""
        try:
            record = UserActivityLog(
                tenant_id=tenant_id,
                user_id=user_id,
                activity_type=activity_type,
                page_path=page_path[:500],
                page_title=page_title[:255],
                session_id=session_id[:64],
                duration_seconds=duration,
                metadata_json=metadata or {},
                device_info=device_info[:255],
                ip_address=ip_address[:45],
            )
            db.session.add(record)
            db.session.commit()
            return {"success": True, "id": record.id}
        except Exception as e:
            logger.error("Failed to log activity: %s", e)
            db.session.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_user_today_stats(tenant_id: int, user_id: int) -> dict:
        """Return aggregated stats for today."""
        try:
            today = date.today()
            today_start = datetime(today.year, today.month, today.day)
            today_end = today_start + timedelta(days=1)

            # Count and aggregate from raw activities
            activities = db.session.query(UserActivityLog).filter(
                UserActivityLog.tenant_id == tenant_id,
                UserActivityLog.user_id == user_id,
                UserActivityLog.created_at >= today_start,
                UserActivityLog.created_at < today_end,
            ).all()

            total_minutes = sum(a.duration_seconds for a in activities) // 60
            total_sessions = len(set(a.session_id for a in activities if a.session_id))
            bird_queries = sum(1 for a in activities if a.activity_type == "bird_ai_query")
            mood_checkins = sum(1 for a in activities if a.activity_type == "mood_checkin")
            relationship_touches = sum(1 for a in activities if a.activity_type == "relationship_touch")
            entertainment_mins = sum(a.duration_seconds for a in activities if a.activity_type == "entertainment") // 60
            social_mins = sum(a.duration_seconds for a in activities if a.activity_type == "social_media") // 60
            focus_mins = sum(a.duration_seconds for a in activities if a.activity_type == "focus_time") // 60
            break_mins = sum(a.duration_seconds for a in activities if a.activity_type == "break") // 60
            pages = list(set(a.page_path for a in activities if a.page_path))

            # Get mood status
            mood = db.session.query(UserMoodCheckin).filter(
                UserMoodCheckin.tenant_id == tenant_id,
                UserMoodCheckin.user_id == user_id,
                UserMoodCheckin.created_at >= today_start,
                UserMoodCheckin.created_at < today_end,
            ).order_by(UserMoodCheckin.created_at.desc()).first()

            return {
                "date": today.isoformat(),
                "total_active_minutes": total_minutes,
                "total_sessions": total_sessions,
                "bird_ai_queries": bird_queries,
                "mood_entries": mood_checkins,
                "relationship_touches": relationship_touches,
                "entertainment_minutes": entertainment_mins,
                "social_media_minutes": social_mins,
                "focus_minutes": focus_mins,
                "break_minutes": break_mins,
                "pages_visited": pages,
                "pages_count": len(pages),
                "current_mood": mood.to_dict() if mood else None,
            }
        except Exception as e:
            logger.error("Failed to get today stats: %s", e)
            return {"error": str(e), "date": date.today().isoformat()}

    @staticmethod
    def get_user_activity_trend(tenant_id: int, user_id: int, days: int = 7) -> list:
        """Return daily activity breakdown for the last N days."""
        try:
            results = []
            for i in range(days - 1, -1, -1):
                day = date.today() - timedelta(days=i)
                day_start = datetime(day.year, day.month, day.day)
                day_end = day_start + timedelta(days=1)

                activities = db.session.query(UserActivityLog).filter(
                    UserActivityLog.tenant_id == tenant_id,
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.created_at >= day_start,
                    UserActivityLog.created_at < day_end,
                ).all()

                total_mins = sum(a.duration_seconds for a in activities) // 60
                bird_q = sum(1 for a in activities if a.activity_type == "bird_ai_query")
                focus_m = sum(a.duration_seconds for a in activities if a.activity_type == "focus_time") // 60
                enter_m = sum(a.duration_seconds for a in activities if a.activity_type == "entertainment") // 60
                social_m = sum(a.duration_seconds for a in activities if a.activity_type == "social_media") // 60
                rel_t = sum(1 for a in activities if a.activity_type == "relationship_touch")

                # Get mood for that day
                mood = db.session.query(UserMoodCheckin).filter(
                    UserMoodCheckin.tenant_id == tenant_id,
                    UserMoodCheckin.user_id == user_id,
                    UserMoodCheckin.created_at >= day_start,
                    UserMoodCheckin.created_at < day_end,
                ).order_by(UserMoodCheckin.created_at.desc()).first()

                results.append({
                    "date": day.isoformat(),
                    "day_name": day.strftime("%a"),
                    "total_minutes": total_mins,
                    "bird_ai_queries": bird_q,
                    "focus_minutes": focus_m,
                    "entertainment_minutes": enter_m,
                    "social_media_minutes": social_m,
                    "relationship_touches": rel_t,
                    "mood": mood.mood if mood else None,
                    "mood_energy": mood.energy if mood else None,
                })
            return results
        except Exception as e:
            logger.error("Failed to get trend: %s", e)
            return []

    @staticmethod
    def get_user_focus_score(tenant_id: int, user_id: int) -> dict:
        """Compute focus score based on recent activity patterns."""
        try:
            today = date.today()
            week_ago = datetime(today.year, today.month, today.day) - timedelta(days=7)

            activities = db.session.query(UserActivityLog).filter(
                UserActivityLog.tenant_id == tenant_id,
                UserActivityLog.user_id == user_id,
                UserActivityLog.created_at >= week_ago,
            ).all()

            focus = sum(a.duration_seconds for a in activities if a.activity_type == "focus_time") // 60
            entertainment = sum(a.duration_seconds for a in activities if a.activity_type == "entertainment") // 60
            social = sum(a.duration_seconds for a in activities if a.activity_type == "social_media") // 60
            total_tracked = focus + entertainment + social

            if total_tracked == 0:
                return {"score": 50, "focus_minutes": focus, "total_tracked_minutes": 0, "status": "insufficient_data"}

            # Focus score: what % of tracked time was focus
            raw_score = (focus / total_tracked) * 100 if total_tracked > 0 else 50
            score = min(100, max(0, round(raw_score)))

            if score >= 70:
                level = "high"
                message = "Great focus! You're spending most of your time on productive work."
            elif score >= 40:
                level = "medium"
                message = "Moderate focus. Consider reducing entertainment/social time during work hours."
            else:
                level = "low"
                message = "Low focus detected. Your tracked time is mostly entertainment and social media."

            return {
                "score": score,
                "focus_minutes": focus,
                "entertainment_minutes": entertainment,
                "social_media_minutes": social,
                "total_tracked_minutes": total_tracked,
                "level": level,
                "message": message,
            }
        except Exception as e:
            logger.error("Failed to compute focus score: %s", e)
            return {"score": 0, "error": str(e)}

    @staticmethod
    def get_relationship_building_score(tenant_id: int, user_id: int, days: int = 30) -> dict:
        """Compute relationship building score."""
        try:
            today = date.today()
            start = datetime(today.year, today.month, today.day) - timedelta(days=days)

            touches = db.session.query(UserActivityLog).filter(
                UserActivityLog.tenant_id == tenant_id,
                UserActivityLog.user_id == user_id,
                UserActivityLog.activity_type == "relationship_touch",
                UserActivityLog.created_at >= start,
            ).count()

            queries = db.session.query(UserActivityLog).filter(
                UserActivityLog.tenant_id == tenant_id,
                UserActivityLog.user_id == user_id,
                UserActivityLog.created_at >= start,
                UserActivityLog.activity_type.in_(["bird_ai_query", "page_view"]),
                UserActivityLog.page_path.like("/relationships%"),
            ).count()

            total_engagement = touches + queries

            # Score: up to 100 based on touches + queries
            score = min(100, total_engagement * 10)

            if total_engagement > 10:
                level = "strong"
                message = f"Strong relationship building! {touches} touches in {days} days."
            elif total_engagement > 3:
                level = "moderate"
                message = f"Moderate relationship building. {touches} touches in {days} days. Try to increase engagement."
            else:
                level = "low"
                message = f"Low relationship building activity. {touches} touches in {days} days. Visit the Relationships module."

            return {
                "score": score,
                "total_touches": touches,
                "relationship_visits": queries,
                "level": level,
                "message": message,
                "period_days": days,
            }
        except Exception as e:
            logger.error("Failed to compute relationship score: %s", e)
            return {"score": 0, "error": str(e)}

    @staticmethod
    def get_mood_trend_with_activity(tenant_id: int, user_id: int, days: int = 7) -> dict:
        """Correlate mood with activity patterns."""
        try:
            trend = UserIntelligence.get_user_activity_trend(tenant_id, user_id, days)
            with_mood = [d for d in trend if d.get("mood")]

            if not with_mood:
                return {"days": trend, "correlation_available": False, "summary": "Not enough mood data to correlate."}

            # Mood score mapping
            mood_values = {"great": 5, "good": 4, "okay": 3, "rough": 2, "tough": 1}
            scores = []
            for d in with_mood:
                mv = mood_values.get(d.get("mood", ""), 3)
                scores.append({
                    "date": d["date"],
                    "mood_score": mv,
                    "mood_label": d["mood"],
                    "focus_minutes": d["focus_minutes"],
                    "entertainment_minutes": d["entertainment_minutes"],
                })

            avg_mood = round(sum(s["mood_score"] for s in scores) / len(scores), 1)
            avg_focus = round(sum(s["focus_minutes"] for s in scores) / len(scores), 0)

            summary = f"Average mood {avg_mood}/5 over {len(scores)} check-ins. Average daily focus: {avg_focus} min."

            return {
                "days": trend,
                "mood_days": scores,
                "correlation_available": len(with_mood) >= 3,
                "average_mood": avg_mood,
                "average_focus": avg_focus,
                "summary": summary,
                "checkin_days": len(with_mood),
            }
        except Exception as e:
            logger.error("Failed to get mood trend: %s", e)
            return {"error": str(e)}

    @staticmethod
    def get_weekly_health_report(tenant_id: int, user_id: int) -> dict:
        """Generate a weekly health + activity report."""
        try:
            today = date.today()
            trend = UserIntelligence.get_user_activity_trend(tenant_id, user_id, 7)
            focus = UserIntelligence.get_user_focus_score(tenant_id, user_id)
            rel = UserIntelligence.get_relationship_building_score(tenant_id, user_id, 7)
            today_stats = UserIntelligence.get_user_today_stats(tenant_id, user_id)

            total_minutes = sum(d.get("total_minutes", 0) for d in trend)
            total_focus = sum(d.get("focus_minutes", 0) for d in trend)
            total_mood = sum(1 for d in trend if d.get("mood"))
            total_bird = sum(d.get("bird_ai_queries", 0) for d in trend)
            avg_entertainment = round(sum(d.get("entertainment_minutes", 0) for d in trend) / max(len(trend), 1), 0)

            # Build the report
            parts = []
            if total_focus >= 120:
                parts.append(f"Great focus this week — {total_focus} minutes of concentrated work.")
            elif total_focus >= 60:
                parts.append(f"Moderate focus this week: {total_focus} minutes.")
            else:
                parts.append(f"Low focus this week ({total_focus} min). Try to dedicate more time to concentrated work.")

            if total_mood >= 3:
                parts.append(f"You checked in {total_mood} times. Keep tracking for mood patterns.")
            elif total_mood > 0:
                parts.append(f"{total_mood} mood check-in(s) this week. Daily check-ins give better insights.")
            else:
                parts.append("No mood check-ins this week. Start tracking your mood daily!")

            if rel.get("total_touches", 0) > 0:
                parts.append(f"{rel['total_touches']} relationship touches this week.")
            else:
                parts.append("No relationship touches this week. Visit the Relationships module.")

            if avg_entertainment >= 60:
                parts.append(f"⚠️ High entertainment time: ~{avg_entertainment} min/day. Consider setting limits.")
            elif avg_entertainment >= 30:
                parts.append(f"Moderate entertainment: ~{avg_entertainment} min/day.")
            else:
                parts.append(f"Low entertainment time (~{avg_entertainment} min/day) — good discipline.")

            parts.append(f"You asked Bird AI {total_bird} queries this week.")

            # Weekly summary
            return {
                "report": " ".join(parts),
                "period": f"{(today - timedelta(days=6)).isoformat()} to {today.isoformat()}",
                "total_active_minutes": total_minutes,
                "total_focus_minutes": total_focus,
                "total_bird_queries": total_bird,
                "mood_checkins": total_mood,
                "focus_score": focus.get("score", 50),
                "relationship_score": rel.get("score", 0),
                "relationship_touches": rel.get("total_touches", 0),
                "avg_daily_entertainment": avg_entertainment,
                "days_reported": len(trend),
            }
        except Exception as e:
            logger.error("Failed to generate weekly report: %s", e)
            return {"report": f"Error generating report: {str(e)}", "error": str(e)}
