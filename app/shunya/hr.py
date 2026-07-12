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


# ---------------------------------------------------------------------------
# Auto-seed sample data for new tenants
# ---------------------------------------------------------------------------

def _seed_sample_data(tenant_id: int):
    """Create sample HR entities if none exist for this tenant.

    Seeds departments, employees (with realistic Indian names), leave requests,
    attendance records, and performance reviews so the dashboard has data.
    """
    dept_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="department"
    ).first()
    if not dept_def:
        return

    existing_count = db.session.query(db.func.count(Entity.id)).filter_by(
        tenant_id=tenant_id, definition_id=dept_def.id
    ).scalar() or 0

    if existing_count > 0:
        return  # Already seeded

    now = __import__("datetime").datetime.utcnow()

    # -----------------------------------------------------------------------
    # 1. Departments
    # -----------------------------------------------------------------------
    departments_data = [
        {"name": "Engineering",        "code": "ENG", "description": "Software development, infrastructure, and platform engineering.",              "budget": 50000000,  "location": "Bangalore"},
        {"name": "Marketing",         "code": "MKT", "description": "Brand management, growth marketing, and communications.",                   "budget": 30000000,  "location": "Mumbai"},
        {"name": "Sales",             "code": "SLS", "description": "Enterprise and SMB sales across India and APAC.",                            "budget": 40000000,  "location": "Delhi"},
        {"name": "Human Resources",   "code": "HR",  "description": "Talent acquisition, people operations, and culture.",                        "budget": 15000000,  "location": "Bangalore"},
        {"name": "Finance",           "code": "FIN", "description": "Accounting, budgeting, financial planning, and compliance.",                  "budget": 12000000,  "location": "Mumbai"},
        {"name": "Product",           "code": "PRD", "description": "Product strategy, roadmap, and user research.",                              "budget": 25000000,  "location": "Bangalore"},
        {"name": "Operations",        "code": "OPS", "description": "Logistics, administration, and facilities management.",                       "budget": 18000000,  "location": "Chennai"},
        {"name": "Design",            "code": "DSN", "description": "UI/UX design, brand identity, and creative services.",                       "budget": 10000000,  "location": "Bangalore"},
    ]

    sample_depts = []
    for i, d in enumerate(departments_data):
        sample_depts.append(Entity(
            tenant_id=tenant_id, definition_id=dept_def.id,
            code=f"DEPT-{i:04d}",
            status="active",
            data={
                "name": d["name"],
                "code": d["code"],
                "description": d["description"],
                "budget": d["budget"],
                "location": d["location"],
            },
        ))

    # -----------------------------------------------------------------------
    # 2. Employees (with manager hierarchy)
    # -----------------------------------------------------------------------
    emp_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="employee"
    ).first()
    if not emp_def:
        # Roll back dept additions
        return

    # (name, employee_code, email, phone, dept, position, salary, emp_type, location)
    # First 8 are directors/managers; the rest are ICs
    employees_data = [
        # Directors / Department Heads (no manager)
        ("Arvind Mehta",       "EMP-001", "arvind.mehta@shunya.io",     "+91-98765-41001", "Engineering",        "Director of Engineering",      2800000, "full_time", "Bangalore"),
        ("Priya Sharma",       "EMP-002", "priya.sharma@shunya.io",    "+91-98765-41002", "Marketing",          "Director of Marketing",        2600000, "full_time", "Mumbai"),
        ("Vikram Singh",       "EMP-003", "vikram.singh@shunya.io",    "+91-98765-41003", "Sales",              "Director of Sales",            2700000, "full_time", "Delhi"),
        ("Ananya Patel",       "EMP-004", "ananya.patel@shunya.io",    "+91-98765-41004", "Human Resources",    "Director of HR",               2200000, "full_time", "Bangalore"),
        ("Rajesh Kumar",       "EMP-005", "rajesh.kumar@shunya.io",    "+91-98765-41005", "Finance",            "Director of Finance",          2500000, "full_time", "Mumbai"),
        ("Sneha Reddy",        "EMP-006", "sneha.reddy@shunya.io",     "+91-98765-41006", "Product",            "Director of Product",          2600000, "full_time", "Bangalore"),
        ("Karthik Nair",       "EMP-007", "karthik.nair@shunya.io",    "+91-98765-41007", "Operations",         "Director of Operations",       2300000, "full_time", "Chennai"),
        ("Meera Joshi",        "EMP-008", "meera.joshi@shunya.io",     "+91-98765-41008", "Design",             "Director of Design",           2400000, "full_time", "Bangalore"),
        # Managers reporting to directors
        ("Deepa Krishnan",     "EMP-009", "deepa.k@shunya.io",          "+91-98765-41009", "Engineering",        "Senior Engineering Manager",   1800000, "full_time", "Bangalore"),
        ("Rahul Verma",        "EMP-010", "rahul.verma@shunya.io",      "+91-98765-41010", "Engineering",        "Backend Engineer",             1200000, "full_time", "Bangalore"),
        ("Lakshmi Iyer",       "EMP-011", "lakshmi.iyer@shunya.io",     "+91-98765-41011", "Marketing",          "Marketing Manager",            1500000, "full_time", "Mumbai"),
        ("Sanjay Gupta",       "EMP-012", "sanjay.gupta@shunya.io",     "+91-98765-41012", "Sales",              "Sales Manager",                1600000, "full_time", "Delhi"),
        ("Neha Joshi",         "EMP-013", "neha.joshi@shunya.io",       "+91-98765-41013", "Human Resources",    "HR Business Partner",          1100000, "full_time", "Bangalore"),
        ("Amit Deshmukh",      "EMP-014", "amit.deshmukh@shunya.io",    "+91-98765-41014", "Finance",            "Finance Manager",              1400000, "full_time", "Mumbai"),
        ("Divya Krishnamurthy","EMP-015", "divya.k@shunya.io",          "+91-98765-41015", "Product",            "Product Manager",              1600000, "full_time", "Bangalore"),
        ("Ravi Shankar",       "EMP-016", "ravi.shankar@shunya.io",     "+91-98765-41016", "Operations",         "Operations Manager",           1300000, "full_time", "Chennai"),
        ("Pooja Singhania",    "EMP-017", "pooja.singhania@shunya.io",  "+91-98765-41017", "Design",             "Senior UI/UX Designer",        1400000, "full_time", "Bangalore"),
        # Individual contributors
        ("Vishal Patil",       "EMP-018", "vishal.patil@shunya.io",     "+91-98765-41018", "Engineering",        "Frontend Engineer",            900000,  "full_time", "Bangalore"),
        ("Anjali Menon",       "EMP-019", "anjali.menon@shunya.io",     "+91-98765-41019", "Marketing",          "Content Marketing Specialist",  800000,  "full_time", "Mumbai"),
        ("Rohit Khanna",       "EMP-020", "rohit.khanna@shunya.io",     "+91-98765-41020", "Sales",              "Account Executive",             950000,  "full_time", "Delhi"),
        ("Swati Agarwal",      "EMP-021", "swati.agarwal@shunya.io",    "+91-98765-41021", "Engineering",        "Data Engineer",                 750000,  "full_time", "Bangalore"),
        ("Arun Nambiar",       "EMP-022", "arun.nambiar@shunya.io",     "+91-98765-41022", "Marketing",          "Social Media Manager",          850000,  "full_time", "Mumbai"),
        ("Kavita Desai",       "EMP-023", "kavita.desai@shunya.io",     "+91-98765-41023", "Sales",              "Business Development",          780000,  "full_time", "Delhi"),
        ("Mohan Prasad",       "EMP-024", "mohan.prasad@shunya.io",     "+91-98765-41024", "Engineering",        "DevOps Engineer",              1100000, "full_time", "Bangalore"),
        ("Nandini Rao",        "EMP-025", "nandini.rao@shunya.io",      "+91-98765-41025", "Human Resources",    "Talent Acquisition Specialist", 700000,  "full_time", "Bangalore"),
        ("Siddharth Bose",     "EMP-026", "sid.bose@shunya.io",         "+91-98765-41026", "Finance",            "Accountant",                    650000,  "full_time", "Mumbai"),
        ("Isha Kapoor",        "EMP-027", "isha.kapoor@shunya.io",      "+91-98765-41027", "Product",            "Associate Product Manager",    1000000, "full_time", "Bangalore"),
        ("Ganesh Iyer",        "EMP-028", "ganesh.iyer@shunya.io",      "+91-98765-41028", "Operations",         "Logistics Coordinator",         600000,  "full_time", "Chennai"),
        ("Tara Shetty",        "EMP-029", "tara.shetty@shunya.io",      "+91-98765-41029", "Design",             "Visual Designer",                720000,  "full_time", "Bangalore"),
        ("Rekha Das",          "EMP-030", "rekha.das@shunya.io",        "+91-98765-41030", "Engineering",        "QA Engineer",                    680000,  "full_time", "Bangalore"),
    ]

    sample_employees = []
    for i, e in enumerate(employees_data):
        mgr_id = None
        if i >= 8:
            # First 8 are directors (no manager); others report to someone
            dept_mgr_map = {"Engineering": 1, "Marketing": 2, "Sales": 3, "Human Resources": 4,
                            "Finance": 5, "Product": 6, "Operations": 7, "Design": 8}
            mgr_id = dept_mgr_map.get(e[4])

        sample_employees.append(Entity(
            tenant_id=tenant_id, definition_id=emp_def.id,
            code=e[1],
            status="active",
            data={
                "employee_name": e[0],
                "employee_code": e[1],
                "email": e[2],
                "phone": e[3],
                "department": e[4],
                "position": e[5],
                "salary": e[6],
                "employment_type": e[7],
                "work_location": e[8],
                "manager_id": mgr_id,
                "date_of_joining": (now - __import__("datetime").timedelta(days=__import__("random").randint(30, 730))).strftime("%Y-%m-%d"),
                "date_of_birth": (now.replace(year=now.year - __import__("random").randint(22, 55))).strftime("%Y-%m-%d"),
                "skills": ", ".join(__import__("random").sample(
                    ["Python", "JavaScript", "SQL", "Go", "React", "Docker", "Kubernetes", "AWS",
                     "Figma", "Photoshop", "Illustrator", "Content Strategy", "SEO", "SEM",
                     "CRM", "Negotiation", "Data Analysis", "Tableau", "Excel", "Recruiting",
                     "Payroll", "Budgeting", "Product Strategy", "Agile", "JIRA"], 4)),
                "bank_account": f"HDFC{__import__('random').randint(1000000000, 9999999999)}",
                "emergency_contact": f"+91-9{__import__('random').randint(100000000, 999999999)}",
                "notes": "Seeded during tenant onboarding.",
            },
        ))

    # Flush to get department and employee IDs for relationships below
    for e in sample_depts + sample_employees:
        db.session.add(e)
    db.session.flush()

    # -----------------------------------------------------------------------
    # 3. Leave Requests
    # -----------------------------------------------------------------------
    leave_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="leave_request"
    ).first()
    sample_leaves = []
    if leave_def and sample_employees:
        # Pick a few employees for sample leave requests
        leave_employees = [
            sample_employees[9],   # Rahul Verma
            sample_employees[10],  # Lakshmi Iyer
            sample_employees[12],  # Neha Joshi
            sample_employees[17],  # Vishal Patil
            sample_employees[18],  # Anjali Menon
            sample_employees[20],  # Swati Agarwal
        ]
        leave_types_reasons = [
            ("annual",     "Family vacation to Kerala during Onam."),
            ("sick",       "Down with viral fever, doctor advised 2 days rest."),
            ("personal",   "Need to attend my cousin's wedding in Pune."),
            ("annual",     "Year-end break — visiting hometown in Tamil Nadu."),
            ("sick",       "Medical appointment for a routine check-up."),
            ("personal",   "Housewarming ceremony at our new flat."),
            ("maternity",  "Maternity leave starting next month."),
        ]

        for i, (emp, ltype, reason) in enumerate(zip(
            leave_employees,
            [l for l, _ in leave_types_reasons[:6]],
            [r for _, r in leave_types_reasons[:6]],
        )):
            start = now - __import__("datetime").timedelta(days=__import__("random").randint(5, 60))
            days = __import__("random").randint(1, 5)
            end = start + __import__("datetime").timedelta(days=days - 1)
            status = __import__("random").choice(["pending", "approved", "rejected", "approved_by_manager"])

            sample_leaves.append(Entity(
                tenant_id=tenant_id, definition_id=leave_def.id,
                code=f"LV-{i:04d}",
                status=status,
                data={
                    "employee_id": emp.id,
                    "employee_name": emp.data["employee_name"],
                    "leave_type": ltype,
                    "start_date": start.strftime("%Y-%m-%d"),
                    "end_date": end.strftime("%Y-%m-%d"),
                    "total_days": days,
                    "reason": reason,
                    "approved_by": 1 if status in ("approved", "approved_by_manager") else None,
                    "approval_notes": "Approved." if status in ("approved", "approved_by_manager") else "",
                },
            ))

    # -----------------------------------------------------------------------
    # 4. Attendance Records (last 30 days for a few employees)
    # -----------------------------------------------------------------------
    att_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="attendance"
    ).first()
    sample_attendance = []
    if att_def and sample_employees:
        attendance_employees = sample_employees[:15]  # First 15 employees
        for i in range(60):  # ~60 records across employees
            emp = __import__("random").choice(attendance_employees)
            day = now - __import__("datetime").timedelta(days=__import__("random").randint(0, 29))
            status = __import__("random").choices(
                ["present", "present", "present", "wfh", "late", "absent", "half_day"],
                weights=[35, 35, 35, 15, 8, 4, 3], k=1
            )[0]
            check_in_h = __import__('random').randint(0, 59)
            check_out_h = __import__('random').randint(0, 59)
            check_in = f"09:{check_in_h:02d} AM" if status in ("present", "wfh") else (f"10:{__import__('random').randint(0, 45):02d} AM" if status == "late" else "")
            check_out = f"06:{check_out_h:02d} PM" if status in ("present", "wfh") else (f"02:{__import__('random').randint(0, 30):02d} PM" if status == "half_day" else "")
            total_hours = 9.0 if status in ("present", "wfh") else 4.5 if status == "half_day" else 0.0

            sample_attendance.append(Entity(
                tenant_id=tenant_id, definition_id=att_def.id,
                code=f"ATT-{i:04d}",
                status=status,
                data={
                    "employee_id": emp.id,
                    "employee_name": emp.data["employee_name"],
                    "date": day.strftime("%Y-%m-%d"),
                    "check_in": check_in,
                    "check_out": check_out,
                    "total_hours": total_hours,
                    "late_minutes": __import__("random").randint(10, 90) if status == "late" else 0,
                    "overtime_hours": round(__import__("random").uniform(0, 3), 1) if status == "present" else 0,
                    "notes": "",
                },
            ))

    # -----------------------------------------------------------------------
    # 5. Performance Reviews (for a subset of employees)
    # -----------------------------------------------------------------------
    perf_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="performance_review"
    ).first()
    sample_reviews = []
    if perf_def and sample_employees:
        review_employees = sample_employees[:12]
        for i, emp in enumerate(review_employees):
            rating = __import__("random").choice(["3", "4", "5"])
            sample_reviews.append(Entity(
                tenant_id=tenant_id, definition_id=perf_def.id,
                code=f"REV-{i:04d}",
                status=__import__("random").choice(["completed", "completed", "acknowledged", "submitted"]),
                data={
                    "employee_id": emp.id,
                    "employee_name": emp.data["employee_name"],
                    "review_period": f"Q{__import__('random').randint(1, 4)} FY{now.year if now.month > 3 else now.year - 1}",
                    "reviewer_id": i + 1 if i < 8 else None,
                    "reviewer_name": employees_data[min(i, 7)][0],
                    "rating": rating,
                    "technical_skills": __import__("random").randint(3, 5),
                    "communication": __import__("random").randint(3, 5),
                    "teamwork": __import__("random").randint(3, 5),
                    "leadership": __import__("random").randint(2, 5),
                    "achievements": "Delivered key milestones ahead of schedule." if int(rating) >= 4 else "Met project deadlines consistently.",
                    "areas_for_improvement": "Could benefit from cross-team collaboration." if int(rating) < 4 else "",
                    "goals_next_period": "Lead a major initiative and mentor junior team members.",
                    "review_date": (now - __import__("datetime").timedelta(days=__import__("random").randint(5, 90))).strftime("%Y-%m-%d"),
                },
            ))

    # -----------------------------------------------------------------------
    # 6. Positions
    # -----------------------------------------------------------------------
    pos_def = db.session.query(EntityDefinition).filter_by(
        tenant_id=tenant_id, type="position"
    ).first()
    sample_positions = []
    if pos_def:
        positions_data = [
            ("Senior Backend Engineer",  "Engineering",        "Director of Engineering",      1500000, 2200000, 5, 3),
            ("Frontend Engineer",        "Engineering",        "Senior Engineering Manager",    600000, 1200000, 8, 4),
            ("Marketing Manager",        "Marketing",          "Director of Marketing",        1200000, 1800000, 3, 2),
            ("Sales Manager",            "Sales",              "Director of Sales",            1300000, 1900000, 4, 2),
            ("HR Business Partner",       "Human Resources",    "Director of HR",                800000, 1300000, 3, 1),
            ("Product Manager",          "Product",            "Director of Product",          1400000, 2000000, 4, 2),
            ("UI/UX Designer",           "Design",             "Director of Design",            700000, 1500000, 5, 3),
            ("Accountant",               "Finance",            "Director of Finance",            500000,  900000, 3, 1),
        ]
        for i, p in enumerate(positions_data):
            sample_positions.append(Entity(
                tenant_id=tenant_id, definition_id=pos_def.id,
                code=f"POS-{i:04d}",
                status="active",
                data={
                    "title": p[0],
                    "department": p[1],
                    "reports_to": p[2],
                    "salary_range_min": p[3],
                    "salary_range_max": p[4],
                    "head_count": p[5],
                    "filled_positions": p[6],
                },
            ))

    # -----------------------------------------------------------------------
    # Commit everything
    # -----------------------------------------------------------------------
    all_entities = sample_depts + sample_employees + sample_leaves + sample_attendance + sample_reviews + sample_positions
    for entity in all_entities:
        db.session.add(entity)
    db.session.commit()
