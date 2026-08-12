"""Generic Entity base model — abstraction layer for any business entity."""
from app import db


class Entity(db.Model):
    __tablename__ = "entities"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50))
    data = db.Column(db.JSON)

    def __repr__(self):
        return f"<Entity #{self.id} [{self.type}] state={self.state}>"