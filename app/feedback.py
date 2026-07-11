"""Shunya OS — AI Feedback Loop (learn from corrections, confidence scoring)."""
from typing import Optional
from datetime import datetime
from flask import g
from app import db
from app.models import AIFeedback, KnowledgeEntry


class FeedbackEngine:
    """Handles user feedback on AI responses — thumbs, corrections, analytics."""

    @staticmethod
    def record_feedback(tenant_id: int, user_id: Optional[int],
                        query: str, response: str,
                        rating: int = None, correction: str = None,
                        knowledge_entry_id: int = None) -> dict:
        """Record user feedback on an AI response.
        
        rating: 1 = thumbs up, -1 = thumbs down, None = no rating
        correction: user's corrected answer (if thumbs down)
        """
        fb = AIFeedback(
            tenant_id=tenant_id,
            user_id=user_id,
            query=query[:2000],
            response=response[:5000],
            rating=rating,
            correction=correction[:2000] if correction else None,
            knowledge_entry_id=knowledge_entry_id,
        )
        db.session.add(fb)

        # If user provided a correction, update the knowledge base
        if correction and knowledge_entry_id:
            entry = db.session.get(KnowledgeEntry, knowledge_entry_id)
            if entry:
                entry.answer = correction
                entry.confidence = min(entry.confidence + 0.1, 1.0)
                entry.verified_by = user_id

        # If correction without existing entry, create one
        elif correction and not knowledge_entry_id:
            # Normalize the question
            q_normalized = query.lower().strip()
            existing = KnowledgeEntry.query.filter_by(
                tenant_id=tenant_id, question=q_normalized
            ).first()
            if existing:
                existing.answer = correction
                existing.confidence = min(existing.confidence + 0.2, 1.0)
                existing.verified_by = user_id
            else:
                entry = KnowledgeEntry(
                    tenant_id=tenant_id,
                    question=q_normalized,
                    answer=correction,
                    source="correction",
                    confidence=0.9,
                    verified_by=user_id,
                )
                db.session.add(entry)

        db.session.commit()

        return {"status": "recorded", "feedback_id": fb.id}

    @staticmethod
    def get_accuracy_stats(tenant_id: int, days: int = 30) -> dict:
        """Get accuracy statistics for the AI over a period."""
        from sqlalchemy import func

        total = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.created_at >= datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        ).count()

        positive = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.rating == 1,
            AIFeedback.created_at >= datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        ).count()

        negative = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.rating == -1,
        ).count()

        # Most common corrections
        corrections = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.correction.isnot(None),
        ).order_by(AIFeedback.created_at.desc()).limit(10).all()

        total_responses = total
        accuracy = positive / total_responses if total_responses > 0 else 0

        return {
            "total_responses": total_responses,
            "positive": positive,
            "negative": negative,
            "accuracy_rate": round(accuracy, 3),
            "recent_corrections": [
                {"query": c.query[:100], "correction": c.correction[:100]}
                for c in corrections
            ],
        }

    @staticmethod
    def get_confidence_label(confidence: float) -> str:
        """Convert a confidence score to a human-readable label."""
        if confidence >= 0.9:
            return "High"
        elif confidence >= 0.7:
            return "Medium-High"
        elif confidence >= 0.5:
            return "Medium"
        elif confidence >= 0.3:
            return "Low-Medium"
        else:
            return "Low"