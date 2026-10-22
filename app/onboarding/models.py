"""Persistence for the onboarding questionnaire session (G1.21).

The questionnaire engine kept its state in a module-level dict — ``_sessions`` —
with the comment "In-memory for now; persists within a session". A reload served
by another worker, or any restart, therefore lost the answers and restarted at the
first question, so "save and resume" was not a product behaviour.

One row per (organization, identity): the questionnaire is organization-scoped by
design (the answers build the organization's business profile).
"""

from datetime import datetime

from app import db


class OnboardingSessionState(db.Model):
    __tablename__ = "onboarding_sessions"
    __table_args__ = (
        db.UniqueConstraint("organization_id", "identity_id",
                            name="uq_onboarding_session_identity"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    identity_id = db.Column(db.String(128), nullable=False, index=True)
    stage = db.Column(db.Integer, nullable=False, default=1)
    question_index = db.Column(db.Integer, nullable=False, default=0)
    answers_json = db.Column(db.Text, nullable=False, default="{}")
    completed_stages_json = db.Column(db.Text, nullable=False, default="[]")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)
