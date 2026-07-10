"""
Panchi Club — Dynamic Fields System (Phase 3D)

Superadmin can create custom fields for any entity (lead, payment, invoice, supplier)
without code changes. Fields can be text, number, date, dropdown, multi-select, or boolean.
Values are stored as JSON and rendered dynamically in forms and detail views.
"""

import json
from datetime import datetime

from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, ForeignKey


class DynamicField(db.Model):
    """Field definition — created by superadmin."""
    __tablename__ = "dynamic_fields"
    __table_args__ = (Index("ix_df_entity", "entity", "field_name"),)

    id = Column(Integer, primary_key=True)
    entity = Column(String(60), nullable=False, index=True)   # lead, payment, invoice, supplier
    field_name = Column(String(120), nullable=False)
    field_label = Column(String(120), nullable=False)
    field_type = Column(String(30), default="text")           # text, number, date, dropdown, multi_select, boolean
    options = Column(Text, default="[]")                      # JSON array for dropdown/multi_select options
    is_required = Column(Boolean, default=False)
    placeholder = Column(String(255), default="")
    help_text = Column(String(500), default="")
    show_in_form = Column(Boolean, default=True)
    show_in_detail = Column(Boolean, default=True)
    searchable = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class DynamicFieldValue(db.Model):
    """Value for a dynamic field on a specific entity instance."""
    __tablename__ = "dynamic_field_values"
    __table_args__ = (Index("ix_dfv_field_entity", "field_id", "entity_id"),)

    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("dynamic_fields.id"), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)   # lead_id, payment_id, etc.
    value = Column(Text, default="")                           # JSON-serialized
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DynamicFieldManager:
    """Manages dynamic field CRUD and value storage."""

    VALID_TYPES = {"text", "number", "date", "dropdown", "multi_select", "boolean"}
    VALID_ENTITIES = {"lead", "payment", "invoice", "supplier"}

    @staticmethod
    def create_field(entity: str, field_name: str, field_label: str,
                     field_type: str = "text", options: list = None,
                     is_required: bool = False, placeholder: str = "",
                     help_text: str = "", show_in_form: bool = True,
                     show_in_detail: bool = True, searchable: bool = False) -> DynamicField:
        if entity not in DynamicFieldManager.VALID_ENTITIES:
            raise ValueError(f"Invalid entity: {entity}")
        if field_type not in DynamicFieldManager.VALID_TYPES:
            raise ValueError(f"Invalid field type: {field_type}")
        if field_type in ("dropdown", "multi_select") and not options:
            raise ValueError(f"Options required for {field_type} fields")

        field = DynamicField(
            entity=entity, field_name=field_name, field_label=field_label,
            field_type=field_type, options=json.dumps(options or []),
            is_required=is_required, placeholder=placeholder,
            help_text=help_text, show_in_form=show_in_form,
            show_in_detail=show_in_detail, searchable=searchable,
        )
        db.session.add(field)
        db.session.commit()
        return field

    @staticmethod
    def get_fields(entity: str, include_hidden: bool = False) -> list[DynamicField]:
        query = DynamicField.query.filter_by(entity=entity)
        if not include_hidden:
            query = query.filter_by(show_in_form=True)
        return query.order_by(DynamicField.sort_order, DynamicField.id).all()

    @staticmethod
    def delete_field(field_id: int) -> bool:
        field = db.session.get(DynamicField, field_id)
        if not field:
            return False
        DynamicFieldValue.query.filter_by(field_id=field_id).delete()
        db.session.delete(field)
        db.session.commit()
        return True

    @staticmethod
    def set_value(field_id: int, entity_id: int, value) -> DynamicFieldValue:
        existing = DynamicFieldValue.query.filter_by(field_id=field_id, entity_id=entity_id).first()
        if existing:
            existing.value = json.dumps(value) if not isinstance(value, str) else value
            existing.updated_at = datetime.utcnow()
        else:
            existing = DynamicFieldValue(
                field_id=field_id, entity_id=entity_id,
                value=json.dumps(value) if not isinstance(value, str) else value,
            )
            db.session.add(existing)
        db.session.commit()
        return existing

    @staticmethod
    def get_values(entity_id: int, entity: str = None) -> dict:
        fields = DynamicField.query
        if entity:
            fields = fields.filter_by(entity=entity)
        fields = fields.all()
        field_ids = [f.id for f in fields]
        if not field_ids:
            return {}
        values = DynamicFieldValue.query.filter(
            DynamicFieldValue.field_id.in_(field_ids),
            DynamicFieldValue.entity_id == entity_id,
        ).all()
        val_map = {v.field_id: v.value for v in values}

        result = {}
        for f in fields:
            raw = val_map.get(f.id)
            if raw is not None:
                try:
                    result[f.field_name] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    result[f.field_name] = raw
            else:
                result[f.field_name] = None
        return result

    @staticmethod
    def search(query_str: str, entity: str = None) -> list[dict]:
        q = f"%{query_str}%"
        field_query = DynamicField.query.filter_by(searchable=True)
        if entity:
            field_query = field_query.filter_by(entity=entity)
        fields = field_query.all()
        results = []
        for f in fields:
            vals = DynamicFieldValue.query.filter(
                DynamicFieldValue.field_id == f.id,
                DynamicFieldValue.value.ilike(q),
            ).all()
            for v in vals:
                results.append({
                    "entity": f.entity, "field": f.field_name,
                    "entity_id": v.entity_id, "value": v.value,
                })
        return results