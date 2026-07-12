"""Shunya HR & People Module — Employee, Department, Leave, Attendance, Performance, Position.

Every organisation needs people management. This module provides:
- Employee lifecycle (onboarding → active → offboarding)
- Department hierarchy and team structure
- Leave management with approvals
- Attendance tracking
- Performance reviews
- Position / role definitions
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from app import db
from app.models import Entity, EntityDefinition, ActivityLog

# ---------------------------------------------------------------------------
# HR Entity Type Definitions (seeded to EntityDefinition)
# ---------------------------------------------------------------------------

HR_ENTITY_TYPES = {
    "employee": {
        "label": "Employee",
        "icon": "👤",
        "schema": [
            {"name": "employee_name", "label": "Employee Name", "type": "text", "required": True, "searchable": True},
            {"name": "employee_code", "label": "Employee Code", "type": "text", "required": True, "searchable": True},
            {"name": "email", "label": "Email", "type": "email", "required": True, "searchable": True},
            {"name": "phone", "label": "Phone", "type": "phone", "searchable": True},
            {"name": "department", "label": "Department", "type": "text", "searchable": True},
            {"name": "position", "label": "Position", "type": "text", "searchable": True},
            {"name": "manager_id", "label": "Manager ID", "type": "number"},
            {"name": "date_of_joining", "label": "Date of Joining", "type": "date"},
            {"name": "date_of_birth", "label": "Date of Birth", "type": "date"},
            {"name": "employment_type", "label": "Employment Type", "type": "select",
             "options": ["full_time", "part_time", "contract", "intern", "probation"]},
            {"name": "work_location", "label": "Work Location", "type": "text"},
            {"name": "salary", "label": "Salary", "type": "number"},
            {"name": "bank_account", "label": "Bank Account", "type": "text"},
            {"name": "emergency_contact", "label": "Emergency Contact", "type": "text"},
            {"name": "skills", "label": "Skills", "type": "textarea"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["onboarding", "probation", "active", "notice_period", "exited"],
        "layout": "table",
        "searchable_fields": ["employee_name", "employee_code", "email", "phone", "department", "position"],
    },
    "department": {
        "label": "Department",
        "icon": "🏢",
        "schema": [
            {"name": "name", "label": "Department Name", "type": "text", "required": True, "searchable": True},
            {"name": "code", "label": "Department Code", "type": "text", "required": True},
            {"name": "head_employee_id", "label": "Department Head", "type": "number"},
            {"name": "parent_department", "label": "Parent Department", "type": "text"},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "budget", "label": "Annual Budget", "type": "number"},
            {"name": "location", "label": "Location", "type": "text"},
        ],
        "statuses": ["active", "inactive", "dissolved"],
        "layout": "table",
        "searchable_fields": ["name", "code", "description"],
    },
    "leave_request": {
        "label": "Leave Request",
        "icon": "🏖️",
        "schema": [
            {"name": "employee_id", "label": "Employee ID", "type": "number", "required": True},
            {"name": "employee_name", "label": "Employee Name", "type": "text", "required": True, "searchable": True},
            {"name": "leave_type", "label": "Leave Type", "type": "select", "required": True,
             "options": ["annual", "sick", "personal", "maternity", "paternity", "bereavement", "unpaid"]},
            {"name": "start_date", "label": "Start Date", "type": "date", "required": True},
            {"name": "end_date", "label": "End Date", "type": "date", "required": True},
            {"name": "total_days", "label": "Total Days", "type": "number"},
            {"name": "reason", "label": "Reason", "type": "textarea", "required": True},
            {"name": "approved_by", "label": "Approved By", "type": "number"},
            {"name": "approval_notes", "label": "Approval Notes", "type": "textarea"},
        ],
        "statuses": ["pending", "approved_by_manager", "approved", "rejected", "cancelled"],
        "layout": "table",
        "searchable_fields": ["employee_name", "leave_type"],
    },
    "attendance": {
        "label": "Attendance",
        "icon": "📅",
        "schema": [
            {"name": "employee_id", "label": "Employee ID", "type": "number", "required": True},
            {"name": "employee_name", "label": "Employee Name", "type": "text", "required": True, "searchable": True},
            {"name": "date", "label": "Date", "type": "date", "required": True},
            {"name": "check_in", "label": "Check In Time", "type": "text"},
            {"name": "check_out", "label": "Check Out Time", "type": "text"},
            {"name": "total_hours", "label": "Total Hours", "type": "number"},
            {"name": "late_minutes", "label": "Late By (mins)", "type": "number"},
            {"name": "overtime_hours", "label": "Overtime Hours", "type": "number"},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
        "statuses": ["present", "absent", "late", "half_day", "wfh", "holiday", "on_leave"],
        "layout": "table",
        "searchable_fields": ["employee_name"],
    },
    "performance_review": {
        "label": "Performance Review",
        "icon": "⭐",
        "schema": [
            {"name": "employee_id", "label": "Employee ID", "type": "number", "required": True},
            {"name": "employee_name", "label": "Employee Name", "type": "text", "required": True, "searchable": True},
            {"name": "review_period", "label": "Review Period", "type": "text", "required": True},
            {"name": "reviewer_id", "label": "Reviewer ID", "type": "number"},
            {"name": "reviewer_name", "label": "Reviewer Name", "type": "text"},
            {"name": "rating", "label": "Rating", "type": "select",
             "options": ["1", "2", "3", "4", "5"]},
            {"name": "technical_skills", "label": "Technical Skills (1-5)", "type": "number"},
            {"name": "communication", "label": "Communication (1-5)", "type": "number"},
            {"name": "teamwork", "label": "Teamwork (1-5)", "type": "number"},
            {"name": "leadership", "label": "Leadership (1-5)", "type": "number"},
            {"name": "achievements", "label": "Achievements", "type": "textarea"},
            {"name": "areas_for_improvement", "label": "Areas for Improvement", "type": "textarea"},
            {"name": "goals_next_period", "label": "Goals for Next Period", "type": "textarea"},
            {"name": "review_date", "label": "Review Date", "type": "date"},
        ],
        "statuses": ["draft", "submitted", "acknowledged", "completed"],
        "layout": "table",
        "searchable_fields": ["employee_name", "review_period", "reviewer_name"],
    },
    "position": {
        "label": "Position",
        "icon": "🎯",
        "schema": [
            {"name": "title", "label": "Position Title", "type": "text", "required": True, "searchable": True},
            {"name": "department", "label": "Department", "type": "text", "required": True, "searchable": True},
            {"name": "reports_to", "label": "Reports To", "type": "text"},
            {"name": "job_description", "label": "Job Description", "type": "textarea"},
            {"name": "requirements", "label": "Requirements", "type": "textarea"},
            {"name": "salary_range_min", "label": "Salary Range Min", "type": "number"},
            {"name": "salary_range_max", "label": "Salary Range Max", "type": "number"},
            {"name": "head_count", "label": "Head Count", "type": "number"},
            {"name": "filled_positions", "label": "Filled Positions", "type": "number"},
        ],
        "statuses": ["active", "on_hold", "filled", "closed"],
        "layout": "table",
        "searchable_fields": ["title", "department", "job_description"],
    },
}


# ---------------------------------------------------------------------------
# HR Dashboard — Data Aggregation
# ---------------------------------------------------------------------------

class HRDashboard:
    """Aggregates HR data for the dashboard views."""

    @staticmethod
    def get_overview(tenant_id: int) -> Dict[str, Any]:
        """Get all HR metrics for the overview dashboard."""
        return {
            "employee_count": HRDashboard.get_employee_count(tenant_id),
            "department_breakdown": HRDashboard.get_department_breakdown(tenant_id),
            "leave_summary": HRDashboard.get_leave_summary(tenant_id),
            "attendance_rate": HRDashboard.get_attendance_rate(tenant_id),
            "pending_reviews": HRDashboard.get_pending_reviews(tenant_id),
            "recent_activity": HRDashboard.get_recent_activity(tenant_id),
        }

    @staticmethod
    def _get_def(tenant_id: int, entity_type: str):
        """Get entity definition for a type, or None."""
        return db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=entity_type
        ).first()

    @staticmethod
    def get_employee_count(tenant_id: int) -> int:
        """Count active employees."""
        emp_def = HRDashboard._get_def(tenant_id, "employee")
        if not emp_def:
            return 0
        return db.session.query(db.func.count(Entity.id)).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == emp_def.id,
            Entity.is_archived == False,
        ).scalar() or 0

    @staticmethod
    def get_department_breakdown(tenant_id: int) -> List[Dict]:
        """Get employee count per department."""
        emp_def = HRDashboard._get_def(tenant_id, "employee")
        if not emp_def:
            return []
        dept_def = HRDashboard._get_def(tenant_id, "department")
        if not dept_def:
            return []

        employees = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == emp_def.id,
            Entity.is_archived == False,
        ).all()

        dept_names = {}
        depts = db.session.query(Entity).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == dept_def.id,
            Entity.is_archived == False,
        ).all()
        for d in depts:
            dept_names[str(d.id)] = d.data.get("name", f"Dept #{d.id}")

        breakdown = {}
        for emp in employees:
            dept = emp.data.get("department", "Unassigned")
            breakdown[dept] = breakdown.get(dept, 0) + 1

        result = []
        for dept_name, count in sorted(breakdown.items(), key=lambda x: -x[1]):
            result.append({"department": dept_name, "count": count})
        return result

    @staticmethod
    def get_leave_summary(tenant_id: int) -> Dict[str, int]:
        """Get leave counts by status."""
        leave_def = HRDashboard._get_def(tenant_id, "leave_request")
        if not leave_def:
            return {"pending": 0, "approved": 0, "rejected": 0, "total": 0}

        rows = db.session.query(
            Entity.status, db.func.count(Entity.id)
        ).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == leave_def.id,
            Entity.is_archived == False,
        ).group_by(Entity.status).all()

        summary = {"pending": 0, "approved": 0, "rejected": 0, "approved_by_manager": 0, "cancelled": 0, "total": 0}
        for status, count in rows:
            summary[status] = count
            summary["total"] += count
        return summary

    @staticmethod
    def get_attendance_rate(tenant_id: int) -> float:
        """Calculate attendance rate as percentage of present days in last 30 days."""
        att_def = HRDashboard._get_def(tenant_id, "attendance")
        if not att_def:
            return 0.0

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        rows = db.session.query(
            Entity.status, db.func.count(Entity.id)
        ).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == att_def.id,
            Entity.created_at >= thirty_days_ago,
        ).group_by(Entity.status).all()

        total = sum(c for _, c in rows)
        if total == 0:
            return 0.0
        present = sum(c for s, c in rows if s in ("present", "wfh"))
        return round((present / total) * 100, 1)

    @staticmethod
    def get_pending_reviews(tenant_id: int) -> int:
        """Count pending performance reviews."""
        perf_def = HRDashboard._get_def(tenant_id, "performance_review")
        if not perf_def:
            return 0
        return db.session.query(db.func.count(Entity.id)).filter(
            Entity.tenant_id == tenant_id,
            Entity.definition_id == perf_def.id,
            Entity.status.in_(["draft", "submitted"]),
            Entity.is_archived == False,
        ).scalar() or 0

    @staticmethod
    def get_recent_activity(tenant_id: int, limit: int = 10) -> List[Dict]:
        """Get recent HR-related activity log entries."""
        activities = db.session.query(ActivityLog).filter(
            ActivityLog.tenant_id == tenant_id
        ).order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).all()

        return [{
            "id": a.id,
            "action": a.action,
            "detail": a.detail,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        } for a in activities]


# ---------------------------------------------------------------------------
# Ensure HR entity types exist for a tenant
# ---------------------------------------------------------------------------

def ensure_hr_types(tenant_id: int):
    """Ensure all HR entity definitions exist for this tenant."""
    for etype, config in HR_ENTITY_TYPES.items():
        existing = db.session.query(EntityDefinition).filter_by(
            tenant_id=tenant_id, type=etype
        ).first()
        if existing:
            continue
        definition = EntityDefinition(
            tenant_id=tenant_id,
            type=etype,
            label=config["label"],
            label_plural=f"{config['label']}s",
            icon=config["icon"],
            schema=config["schema"],
            statuses=config["statuses"],
            layout=config.get("layout", "table"),
            searchable_fields=config.get("searchable_fields", []),
            primary_field=config["schema"][0]["name"] if config["schema"] else "name",
        )
        db.session.add(definition)
    db.session.commit()
