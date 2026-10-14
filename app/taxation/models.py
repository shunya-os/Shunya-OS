"""Taxation rules engine — auto-refreshing government tax and business law rules."""

from datetime import datetime
from app import db
from sqlalchemy import Index, Text


class TaxRule(db.Model):
    """A single taxation rule from an authoritative government source."""
    __tablename__ = "taxation_rules"
    __table_args__ = (
        Index("ix_tax_rule_org", "organization_id"),
        Index("ix_tax_rule_category", "category"),
        Index("ix_tax_rule_source", "source"),
    )
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    category = db.Column(db.String(60), nullable=False)
    jurisdiction = db.Column(db.String(60), default="IN")
    business_type = db.Column(db.String(60), default="*")
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(Text, default="")
    effective_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    rate = db.Column(db.Float, nullable=True)
    threshold_min = db.Column(db.Float, nullable=True)
    threshold_max = db.Column(db.Float, nullable=True)
    threshold_unit = db.Column(db.String(30), default="INR")
    section = db.Column(db.String(100), default="")
    applicability = db.Column(db.String(100), default="")
    source = db.Column(db.String(255), default="")
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    etag = db.Column(db.String(100), default="")
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)
    superseded_by = db.Column(db.Integer, db.ForeignKey("taxation_rules.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "category": self.category, "jurisdiction": self.jurisdiction,
            "business_type": self.business_type, "title": self.title,
            "description": (self.description or "")[:500],
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "rate": self.rate, "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max, "threshold_unit": self.threshold_unit,
            "section": self.section, "applicability": self.applicability,
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "is_active": self.is_active, "version": self.version,
        }


class BusinessRule(db.Model):
    """General business regulation from government sources."""
    __tablename__ = "taxation_business_rules"
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    category = db.Column(db.String(60), nullable=False)
    jurisdiction = db.Column(db.String(60), default="IN")
    business_type = db.Column(db.String(60), default="*")
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(Text, default="")
    effective_date = db.Column(db.Date, nullable=True)
    deadline_date = db.Column(db.Date, nullable=True)
    section = db.Column(db.String(100), default="")
    source = db.Column(db.String(255), default="")
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "category": self.category, "jurisdiction": self.jurisdiction,
            "business_type": self.business_type, "title": self.title,
            "description": (self.description or "")[:500],
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "deadline_date": self.deadline_date.isoformat() if self.deadline_date else None,
            "section": self.section,
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }


class TaxationRefreshLog(db.Model):
    """Log of 24-hour refresh cycles."""
    __tablename__ = "taxation_refresh_log"
    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    sources_attempted = db.Column(db.Integer, default=0)
    sources_success = db.Column(db.Integer, default=0)
    rules_created = db.Column(db.Integer, default=0)
    error = db.Column(db.String(500), default="")