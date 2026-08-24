"""MediaAsset model — persisted generated media with canonical runtime state."""

from datetime import datetime
from app import db


class MediaAsset(db.Model):
    """Canonical media asset with full runtime state tracking.

    Stores every media generation attempt with its explicit state:
    IDLE -> PREPARING_BRIEF -> GENERATING -> GENERATED / DESCRIPTION_ONLY / PROVIDER_UNAVAILABLE / FAILED

    No GENERATED record may exist without a real asset_url pointing to
    an actual generated image artifact.
    """

    __tablename__ = "m6_media_assets"

    id = db.Column(db.Integer, primary_key=True)
    identity_id = db.Column(db.String(64), nullable=False, index=True)

    # ── Canonical runtime state ──────────────────────────────
    # IDLE | PREPARING_BRIEF | GENERATING | GENERATED | DESCRIPTION_ONLY | PROVIDER_UNAVAILABLE | FAILED
    runtime_state = db.Column(db.String(30), nullable=False, default="idle")

    # ── Result classification ────────────────────────────────
    # generated_image | visual_concept | provider_unavailable | error
    result_kind = db.Column(db.String(30), nullable=True)

    # ── Input ────────────────────────────────────────────────
    raw_prompt = db.Column(db.Text, nullable=False)
    visual_brief = db.Column(db.Text, nullable=True)
    platform = db.Column(db.String(40), nullable=True)
    aspect_ratio = db.Column(db.String(10), default="1:1")
    visual_style = db.Column(db.String(30), default="realistic")

    # ── Business context (structured facts for visual brief) ─
    business_context = db.Column(db.JSON, nullable=True, default=dict)

    # ── Output ───────────────────────────────────────────────
    asset_url = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(40), nullable=True)
    generation_job_id = db.Column(db.String(80), nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)

    # ── Campaign linkage ─────────────────────────────────────
    campaign_id = db.Column(db.Integer, db.ForeignKey("m6_ad_campaigns.id"), nullable=True)

    # ── Timestamps ────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_canonical(self) -> dict:
        """Return the single source of truth result contract."""
        return {
            "id": self.id,
            "runtime_state": self.runtime_state,
            "result_kind": self.result_kind,
            "raw_prompt": self.raw_prompt,
            "visual_brief": self.visual_brief,
            "asset_url": self.asset_url,
            "description": self.description,
            "platform": self.platform,
            "aspect_ratio": self.aspect_ratio,
            "visual_style": self.visual_style,
            "provider": self.provider,
            "generation_job_id": self.generation_job_id,
            "failure_reason": self.failure_reason,
            "campaign_id": self.campaign_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }