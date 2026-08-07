"""
Seed data generator for SHUNYA OS.

Creates sample objects (customers, contacts, invoices, proposals, tasks)
for a given workspace. Designed to be called from the API or app factory
on workspace creation.

Usage:
    from app.objects.seed import seed_workspace
    seed_workspace(workspace_id='spc_business_xxx', identity_id='identity_uuid')
"""

import uuid
from datetime import datetime, timedelta
from app import db
from app.objects.legacy_models import ShunyaObject


def _oid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


def _days(n: int) -> datetime:
    return _now() + timedelta(days=n)


# ── Premium Business Seed Data ─────────────────────────────────


BUSINESS_CUSTOMERS = [
    {'company_name': 'Tesla Motors', 'contact_name': 'Elon Musk', 'email': 'elon@tesla.com', 'phone': '+1-555-0100', 'address': '1 Tesla Road, Austin, TX', 'notes': '$12.5T market cap — flagship client, EV and energy division'},
    {'company_name': 'SpaceX', 'contact_name': 'Gwynne Shotwell', 'email': 'gwynne@spacex.com', 'phone': '+1-555-0101', 'address': '1 Rocket Rd, Hawthorne, CA', 'notes': 'Starship program partner, launch vehicle avionics'},
    {'company_name': 'Adobe Inc.', 'contact_name': 'Shantanu Narayen', 'email': 'shantanu@adobe.com', 'phone': '+1-555-0102', 'address': '345 Park Ave, San Jose, CA', 'notes': 'Enterprise creative suite license, digital experience platform'},
    {'company_name': 'Spotify AB', 'contact_name': 'Daniel Ek', 'email': 'daniel@spotify.com', 'phone': '+1-555-0103', 'address': '150 Greenwich St, New York, NY', 'notes': 'Music streaming leader, API integration and analytics'},
    {'company_name': 'Nike Inc.', 'contact_name': 'John Donahoe', 'email': 'john@nike.com', 'phone': '+1-555-0104', 'address': '1 Bowerman Dr, Beaverton, OR', 'notes': 'Global athletic brand, digital marketing partnership'},
]

BUSINESS_CONTACTS = [
    {'name': 'Elon Musk', 'email': 'elon@tesla.com', 'phone': '+1-555-0100', 'company': 'Tesla Motors', 'notes': 'Key decision maker — CEO'},
    {'name': 'Gwynne Shotwell', 'email': 'gwynne@spacex.com', 'phone': '+1-555-0101', 'company': 'SpaceX', 'notes': 'Operations lead — COO'},
    {'name': 'Shantanu Narayen', 'email': 'shantanu@adobe.com', 'phone': '+1-555-0102', 'company': 'Adobe Inc.', 'notes': 'CEO — strategic partnership contact'},
]

BUSINESS_INVOICES = [
    {'customer_name': 'Tesla Motors', 'invoice_number': 'INV-001', 'amount': 12500.00, 'currency': 'USD', 'issue_date': _now().isoformat(), 'due_date': _days(30).isoformat(), 'status': 'paid', 'notes': 'Q4 digital transformation consulting retainer'},
    {'customer_name': 'SpaceX', 'invoice_number': 'INV-002', 'amount': 42000.00, 'currency': 'USD', 'issue_date': (_now() - timedelta(days=40)).isoformat(), 'due_date': (_now() - timedelta(days=10)).isoformat(), 'status': 'overdue', 'notes': 'Starship avionics contract — milestone 2'},
    {'customer_name': 'Adobe Inc.', 'invoice_number': 'INV-003', 'amount': 8750.00, 'currency': 'USD', 'issue_date': _now().isoformat(), 'due_date': _days(30).isoformat(), 'status': 'sent', 'notes': 'Creative Suite enterprise license renewal'},
    {'customer_name': 'Spotify AB', 'invoice_number': 'INV-004', 'amount': 3200.00, 'currency': 'USD', 'issue_date': (_now() - timedelta(days=5)).isoformat(), 'due_date': _days(25).isoformat(), 'status': 'draft', 'notes': 'API integration services — Phase 1'},
    {'customer_name': 'Nike Inc.', 'invoice_number': 'INV-005', 'amount': 15000.00, 'currency': 'USD', 'issue_date': _now().isoformat(), 'due_date': _days(30).isoformat(), 'status': 'paid', 'notes': 'Digital marketing campaign — Q4 launch'},
]

BUSINESS_PROPOSALS = [
    {'title': 'Q4 Digital Transformation — Tesla Motors', 'customer_name': 'Tesla Motors', 'amount': 125000.00, 'currency': 'USD', 'status': 'sent', 'valid_until': _days(60).isoformat(), 'terms': 'Net 30 — 50% upfront', 'notes': 'Full-stack modernization, supply chain AI, EV analytics platform'},
    {'title': 'Enterprise AI Implementation — SpaceX', 'customer_name': 'SpaceX', 'amount': 450000.00, 'currency': 'USD', 'status': 'draft', 'valid_until': _days(90).isoformat(), 'terms': 'Milestone-based — 4 phases', 'notes': 'Custom ML pipeline for telemetry, predictive launch analytics'},
    {'title': 'Brand Partnership Campaign — Nike', 'customer_name': 'Nike Inc.', 'amount': 75000.00, 'currency': 'USD', 'status': 'draft', 'valid_until': _days(45).isoformat(), 'terms': 'Net 15 — monthly retainer', 'notes': 'Digital experience, athlete endorsements, campaign analytics'},
]

BUSINESS_TASKS = [
    {'title': 'Review Q3 earnings report', 'description': 'Review and analyze Q3 financials for all portfolio companies', 'assignee': 'self', 'due_date': _days(1).isoformat(), 'status': 'in_progress', 'priority': 'high', 'notes': 'Board meeting prep — include Tesla and Nike projections'},
    {'title': 'Prepare board deck for Friday', 'description': 'Create board presentation covering Q4 strategy, pipeline, and key metrics', 'assignee': 'self', 'due_date': _days(3).isoformat(), 'status': 'pending', 'priority': 'high', 'notes': 'Include SpaceX proposal status and Adobe renewal'},
    {'title': 'Call SpaceX about overdue invoice INV-002', 'description': 'Follow up with Gwynne Shotwell regarding $42K overdue invoice', 'assignee': 'self', 'due_date': _now().isoformat(), 'status': 'pending', 'priority': 'high', 'notes': 'Reminder: Starship program contract — milestone payment'},
    {'title': 'Update team on Q4 roadmap', 'description': 'All-hands sync on Q4 roadmap priorities and deliverables', 'assignee': 'self', 'due_date': _days(7).isoformat(), 'status': 'pending', 'priority': 'medium', 'notes': 'Use conference room A, prepare slide deck'},
    {'title': 'Review Adobe proposal feedback', 'description': 'Review notes from Shantanu on enterprise AI proposal and prepare counter', 'assignee': 'self', 'due_date': _days(14).isoformat(), 'status': 'pending', 'priority': 'low', 'notes': 'Creative Suite renewal opportunity — follow up with legal'},
]

# ── Personal Seed Data ─────────────────────────────────────────


PERSONAL_CONTACTS = [
    {'name': 'Mom', 'email': 'mom@example.com', 'phone': '+1-555-1001', 'company': '', 'address': '123 Family Ln', 'notes': 'Call every Sunday'},
    {'name': 'Alex K.', 'email': 'alex.k@example.com', 'phone': '+1-555-1002', 'company': '', 'address': '456 College Ave', 'notes': 'Old college roommate'},
    {'name': 'Dr. Williams', 'email': 'dr.williams@clinic.com', 'phone': '+1-555-1003', 'company': 'City Health Clinic', 'address': '789 Medical Dr', 'notes': 'Annual checkup in March'},
]

PERSONAL_TASKS = [
    {'title': 'Grocery shopping', 'description': 'Weekly groceries — produce, dairy, grains', 'assignee': 'self', 'due_date': _days(2).isoformat(), 'status': 'pending', 'priority': 'medium', 'notes': 'Farmers market on Saturday'},
    {'title': 'Gym session', 'description': 'Cardio + strength training', 'assignee': 'self', 'due_date': _now().isoformat(), 'status': 'completed', 'priority': 'medium', 'notes': 'Morning preferred'},
    {'title': 'Book dentist appointment', 'description': 'Schedule semi-annual cleaning', 'assignee': 'self', 'due_date': _days(14).isoformat(), 'status': 'pending', 'priority': 'low', 'notes': 'Call Dr. Smith office'},
    {'title': 'Read "Atomic Habits"', 'description': 'Finish reading — 100 pages remaining', 'assignee': 'self', 'due_date': _days(21).isoformat(), 'status': 'in_progress', 'priority': 'low', 'notes': 'Chapter 9-12 remaining'},
    {'title': 'Plan weekend trip', 'description': 'Research destinations and book accommodations', 'assignee': 'self', 'due_date': _days(10).isoformat(), 'status': 'pending', 'priority': 'medium', 'notes': 'Beach or mountains?'},
]

# ── Custom Seed Data ───────────────────────────────────────────


CUSTOM_CONTACTS = [
    {'name': 'Jane Doe', 'email': 'jane@example.com', 'phone': '+1-555-2001', 'company': 'Freelance', 'address': '321 Elm St', 'notes': 'Potential collaborator'},
    {'name': 'Bob Wilson', 'email': 'bob@example.com', 'phone': '+1-555-2002', 'company': 'TechStart', 'address': '654 Maple Dr', 'notes': 'Met at conference'},
]

CUSTOM_TASKS = [
    {'title': 'Set up project board', 'description': 'Create kanban board for new project', 'assignee': 'self', 'due_date': _days(3).isoformat(), 'status': 'pending', 'priority': 'high', 'notes': 'Use existing template'},
    {'title': 'Research competitors', 'description': 'Analyze top 3 competitors in market', 'assignee': 'self', 'due_date': _days(7).isoformat(), 'status': 'in_progress', 'priority': 'medium', 'notes': 'Focus on pricing'},
    {'title': 'Draft project proposal', 'description': 'Write initial project proposal document', 'assignee': 'self', 'due_date': _days(14).isoformat(), 'status': 'pending', 'priority': 'medium', 'notes': 'Include timeline and budget'},
]


# ── Seed Functions ─────────────────────────────────────────────


def _create_objects(objects_data: list[dict], workspace_id: str, identity_id: str, object_type: str) -> list[ShunyaObject]:
    """Create ShunyaObject instances from seed data dictionaries.

    The ``status`` key in the seed dict is a *business* status (e.g. 'paid',
    'sent', 'draft', 'in_progress') and is stored *inside* the ``data`` JSON
    column.  The ShunyaObject's own ``status`` column tracks the object's
    lifecycle (active / archived) and is always set to ``'active'`` for
    newly-seeded objects.
    """
    created = []
    for data in objects_data:
        obj = ShunyaObject(
            object_id=_oid(),
            workspace_id=workspace_id,
            object_type=object_type,
            name=data.get('name') or data.get('title') or data.get('company_name') or data.get('customer_name') or object_type,
            status='active',  # lifecycle status — always active for new seed data
            data=data,        # business status stays inside the JSON column
            created_by=identity_id,
        )
        db.session.add(obj)
        created.append(obj)
    return created


def seed_workspace(workspace_id: str, identity_id: str, workspace_type: str = 'business') -> dict:
    """
    Seed a workspace with sample data based on its type.

    If the workspace already has any objects, seeding is skipped to avoid
    duplicate data.

    Args:
        workspace_id: The workspace ID to seed objects under.
        identity_id: The identity creating the objects.
        workspace_type: One of 'business', 'personal', 'custom'.

    Returns:
        dict with keys 'success' and 'created' (count of objects created).
    """
    # Check if workspace already has data — skip if yes
    existing = ShunyaObject.query.filter_by(workspace_id=workspace_id).first()
    if existing:
        return {'success': True, 'created': 0, 'skipped': True}

    created_count = 0

    try:
        if workspace_type == 'business':
            _create_objects(BUSINESS_CUSTOMERS, workspace_id, identity_id, 'customer')
            _create_objects(BUSINESS_INVOICES, workspace_id, identity_id, 'invoice')
            _create_objects(BUSINESS_PROPOSALS, workspace_id, identity_id, 'proposal')
            _create_objects(BUSINESS_TASKS, workspace_id, identity_id, 'task')
            _create_objects(BUSINESS_CONTACTS, workspace_id, identity_id, 'contact')
            created_count = 5 + 5 + 3 + 5 + 3  # 21

        elif workspace_type == 'personal':
            _create_objects(PERSONAL_CONTACTS, workspace_id, identity_id, 'contact')
            _create_objects(PERSONAL_TASKS, workspace_id, identity_id, 'task')
            created_count = 3 + 5  # 8

        else:  # custom
            _create_objects(CUSTOM_CONTACTS, workspace_id, identity_id, 'contact')
            _create_objects(CUSTOM_TASKS, workspace_id, identity_id, 'task')
            created_count = 2 + 3  # 5

        db.session.commit()
        return {'success': True, 'created': created_count}

    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def seed_all_workspaces(identity_id: str) -> dict:
    """
    Seed all workspace types for a given identity.
    Creates sample data in workspaces named 'spc_business', 'spc_personal', 'spc_custom'.

    Args:
        identity_id: The identity creating the objects.

    Returns:
        dict with keys 'success' and 'results' (list of per-workspace results).
    """
    from app.objects.legacy_models import Workspace

    results = []
    workspaces = Workspace.query.filter(
        Workspace.created_by == identity_id,
        Workspace.status == 'active',
    ).all()

    for ws in workspaces:
        result = seed_workspace(ws.id, identity_id, ws.workspace_type)
        result['workspace_id'] = ws.id
        result['workspace_type'] = ws.workspace_type
        results.append(result)

    return {'success': True, 'results': results}