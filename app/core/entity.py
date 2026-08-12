"""Generic Entity base model — abstraction layer for any business entity."""
from app import db


class Entity(db.Model):
    __tablename__ = "entities"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    definition_id = db.Column(db.Integer, nullable=False, default=0)
    code = db.Column(db.String(100))
    status = db.Column(db.String(50))
    assigned_to = db.Column(db.Integer)
    data = db.Column(db.JSON)
    ai_summary = db.Column(db.Text)
    tags = db.Column(db.JSON)
    is_archived = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    code_prefix = db.Column(db.String(20))
    type = db.Column(db.String(50))
    state = db.Column(db.String(50))

    def __repr__(self):
        return f"<Entity #{self.id} [{self.type}] state={self.state}>"