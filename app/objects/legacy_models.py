"""SHUNYA OS — Legacy Phase 0 Models (backward compatibility).

Kept separate from the pure PROD-05 Object model to preserve purity.
Required by existing modules (composer, reality_engine, upload, seed, pdf).
"""

import uuid
from datetime import datetime, timezone

from app import db


def _generate_object_id() -> str:
    return str(uuid.uuid4())


OBJECT_STAGE_PIPELINES: dict[str, list[str]] = {
    "proposal": ["Draft", "Sent", "Under Review", "Accepted", "Declined"],
    "invoice": ["Draft", "Sent", "Paid", "Overdue"],
    "contact": ["Lead", "Active", "Inactive"],
    "task": ["Todo", "In Progress", "Done", "Verified"],
    "note": ["Draft", "Finalized"],
    "contract": ["Draft", "Under Review", "Signed", "Active", "Expired"],
    "meeting": ["Scheduled", "In Progress", "Completed"],
    "document": ["Draft", "Under Review", "Approved", "Published"],
    "project": ["Planning", "In Progress", "Review", "Completed"],
    "event": ["Scheduled", "In Progress", "Completed"],
}

DEFAULT_STAGE_PIPELINE = ["Created", "In Progress", "Completed"]


def get_stage_pipeline(object_type: str) -> list[str]:
    return OBJECT_STAGE_PIPELINES.get(object_type, DEFAULT_STAGE_PIPELINE)


class Workspace(db.Model):
    __tablename__ = 'sh_workspaces'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    workspace_type = db.Column(db.String(20), nullable=False)
    icon = db.Column(db.String(10), default='🏢')
    color = db.Column(db.String(10), default='#6C4AE2')
    description = db.Column(db.String(500), default='')
    created_by = db.Column(db.String(64), nullable=False)
    organization_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'workspace_type': self.workspace_type,
            'icon': self.icon, 'color': self.color, 'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
        }


class ShunyaObject(db.Model):
    __tablename__ = 'sh_objects'
    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.String(36), unique=True, nullable=False, default=_generate_object_id)
    workspace_id = db.Column(db.String(20), db.ForeignKey('sh_workspaces.id'), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(30), default='active')
    data = db.Column(db.JSON, default=dict)
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id, 'object_id': self.object_id, 'workspace_id': self.workspace_id,
            'object_type': self.object_type, 'name': self.name, 'status': self.status,
            'data': self.data or {}, 'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


OBJECT_TYPES = {
    'customer': {
        'name': 'Customer',
        'fields': ['company_name', 'contact_name', 'email', 'phone', 'address', 'notes'],
        'required': ['company_name'], 'name_field': 'company_name',
    },
    'contact': {
        'name': 'Contact',
        'fields': ['name', 'email', 'phone', 'company', 'address', 'notes'],
        'required': ['name'], 'name_field': 'name',
    },
    'invoice': {
        'name': 'Invoice',
        'fields': [
            'customer_name', 'customer_company', 'customer_email', 'customer_address',
            'invoice_number', 'items', 'subtotal', 'discount_type', 'discount_value',
            'discount_amount', 'tax_lines', 'tax_total', 'shipping', 'grand_total',
            'currency', 'issue_date', 'due_date', 'status', 'payment_status',
            'notes', 'payment_terms', 'logo_url', 'bank_details',
            'stripe_link', 'paypal_link', 'qr_code_url',
            'reminder_schedule', 'reminder_history', 'next_reminder_at',
            'is_recurring', 'recurring_frequency', 'recurring_next_date', 'recurring_auto_send',
            'exchange_rate_info',
        ],
        'required': ['customer_name'], 'name_field': 'customer_name',
    },
    'proposal': {
        'name': 'Proposal',
        'fields': [
            'title', 'customer_name', 'amount', 'currency', 'status',
            'valid_until', 'terms', 'notes', 'line_items', 'discount_type',
            'discount_value', 'tax_rate', 'signature_data', 'signature_date',
            'shared_link', 'share_password', 'share_expiry', 'share_accessed',
            'cover_message', 'ai_context',
        ],
        'required': ['title', 'customer_name'], 'name_field': 'title',
    },
    'task': {
        'name': 'Task',
        'fields': ['title', 'description', 'assignee', 'due_date', 'status', 'priority', 'notes'],
        'required': ['title'], 'name_field': 'title',
    },
    'project': {
        'name': 'Project',
        'fields': ['name', 'description', 'deadline', 'status', 'budget', 'notes'],
        'required': ['name'], 'name_field': 'name',
    },
    'employee': {
        'name': 'Employee',
        'fields': ['name', 'email', 'phone', 'role', 'department', 'status', 'notes'],
        'required': ['name', 'email'], 'name_field': 'name',
    },
    'document': {
        'name': 'Document',
        'fields': ['title', 'file_path', 'file_type', 'file_size', 'description', 'tags'],
        'required': ['title'], 'name_field': 'title',
    },
    'note': {
        'name': 'Note',
        'fields': ['title', 'content', 'tags'],
        'required': ['title'], 'name_field': 'title',
    },
}


def resolve_object_name(object_type: str, data: dict) -> str:
    spec = OBJECT_TYPES.get(object_type, {})
    name_field = spec.get('name_field', 'name')
    value = data.get(name_field) or data.get('name') or data.get('title') or ''
    return str(value).strip() or f"{spec.get('name', object_type)} {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"