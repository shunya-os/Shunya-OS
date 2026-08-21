"""Universal Object Protocol — SQLAlchemy persistence model.

Stores UniversalObject instances from the canonical protocol
(app.kernel.object.UniversalObject) in a relational table,
providing the HTTP/API persistence layer.

Every UniversalObject instance maps to one row in sh_uop_objects.
"""
from app import db
from datetime import datetime, timezone


class UOPObject(db.Model):
    """Persistent storage for UniversalObject protocol instances.

    The dataclass-based UniversalObject in app/kernel/object.py defines
    the protocol contract. This model provides SQL persistence and
    queryability while preserving the canonical field set.
    """
    __tablename__ = "sh_uop_objects"

    object_id = db.Column(db.String(64), primary_key=True)
    tenant_id = db.Column(db.Integer, default=0, nullable=False)
    space_id = db.Column(db.String(64), default="", nullable=False)
    object_type = db.Column(db.String(128), default="", nullable=False)
    name = db.Column(db.String(512), default="", nullable=False)
    status = db.Column(db.String(32), default="active", nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    confidence = db.Column(db.Float, default=1.0, nullable=False)
    created_at = db.Column(db.String(64), default="", nullable=False)
    updated_at = db.Column(db.String(64), default="", nullable=False)
    created_by = db.Column(db.String(128), default="", nullable=False)
    updated_by = db.Column(db.String(128), default="", nullable=False)
    evidence_json = db.Column(db.Text, default="[]", nullable=False)
    relationships_json = db.Column(db.Text, default="[]", nullable=False)
    metadata_json = db.Column(db.Text, default="{}", nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    def to_protocol_dict(self) -> dict:
        """Convert back to the UniversalObject protocol dict."""
        import json
        return {
            "object_id": self.object_id,
            "tenant_id": self.tenant_id,
            "space_id": self.space_id,
            "object_type": self.object_type,
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "evidence": json.loads(self.evidence_json or "[]"),
            "relationships": json.loads(self.relationships_json or "[]"),
            "metadata": json.loads(self.metadata_json or "{}"),
        }

    @classmethod
    def from_protocol(cls, obj) -> "UOPObject":
        """Create a UOPObject from a UniversalObject protocol instance."""
        import json
        return cls(
            object_id=obj.object_id,
            tenant_id=obj.tenant_id,
            space_id=obj.space_id,
            object_type=obj.object_type,
            name=obj.name,
            status=obj.status,
            version=obj.version,
            confidence=obj.confidence,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            created_by=obj.created_by,
            updated_by=obj.updated_by,
            evidence_json=json.dumps([e.__dict__ if hasattr(e, '__dict__') else e for e in obj.evidence]),
            relationships_json=json.dumps([r.__dict__ if hasattr(r, '__dict__') else r for r in obj.relationships]),
            metadata_json=json.dumps(obj.metadata),
            is_archived=obj.status == "archived",
        )