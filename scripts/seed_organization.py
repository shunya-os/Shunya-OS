"""
SHUNYA PLP Cycle 3.1 — Seed XYZ Company Organization
Creates the organization, departments, and all members.
"""
import sys, os, json, secrets, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ['DATABASE_URL'] = 'postgresql://shunya:shunya_os_2024@127.0.0.1:5433/shunya_db'

from app import create_app, db
from app.models import Organization, OrgMember, Department
from app.authz.models import Role, OrgMemberRole
from app.auth import TeamMember, UserRole as AuthUserRole
from sqlalchemy import text

app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": os.environ['DATABASE_URL']})

with app.app_context():
    # Verify connection
    assert db.session.execute(text("SELECT 1")).scalar() == 1
    print("Database connected.")

    # 1. Create Organization
    org = Organization.query.filter_by(slug="xyz-company").first()
    if not org:
        org = Organization(
            name="XYZ Company", slug="xyz-company",
            business_type="Professional Services", email="founder@xyzcompany.com",
            phone="+1-555-0100", website="https://xyzcompany.com",
            brand_tagline="Your Trusted Business Partner",
            brand_description="Professional services firm delivering excellence.",
            timezone="UTC", currency="USD", is_active=True, max_members=50, ai_enabled=True,
        )
        db.session.add(org)
        db.session.flush()
    print(f"Organization: {org.name} (id={org.id})")

    # 2. Departments
    dept_defs = {
        "Executive": {"description": "Executive management and strategic direction"},
        "Sales": {"description": "Lead generation, client acquisition, and revenue growth"},
        "Operations": {"description": "Day-to-day operations, logistics, and process management"},
        "Finance": {"description": "Accounting, budgeting, financial reporting, and compliance"},
        "HR": {"description": "Human resources, recruitment, talent management"},
        "Marketing": {"description": "Brand management, digital marketing, content, and campaigns"},
        "Support": {"description": "Customer support, issue resolution, and client success"},
    }
    departments = {}
    for name, info in dept_defs.items():
        dept = Department.query.filter_by(organization_id=org.id, name=name).first()
        if not dept:
            dept = Department(organization_id=org.id, name=name, description=info["description"], is_active=True)
            db.session.add(dept)
            db.session.flush()
        departments[name] = dept
    print(f"Departments: {len(departments)}")

    # 3. Create all members
    members_data = [
        # Founders and Directors
        ("ABC", "founder@xyzcompany.com", "owner", "Founder & CEO", "Executive", True),
        ("David Director", "david@xyzcompany.com", "admin", "Director of Sales", "Sales", True),
        ("Olivia Director", "olivia@xyzcompany.com", "admin", "Director of Operations", "Operations", True),
        ("Felicia Director", "felicia@xyzcompany.com", "admin", "Director of Finance", "Finance", True),
        ("Henry Director", "henry@xyzcompany.com", "admin", "Director of HR", "HR", True),
        # Managers
        ("Maya Manager", "maya@xyzcompany.com", "manager", "Sales Manager", "Sales", False),
        ("Nathan Manager", "nathan@xyzcompany.com", "manager", "Operations Manager", "Operations", False),
        ("Fiona Manager", "fiona@xyzcompany.com", "manager", "Finance Manager", "Finance", False),
        ("Hannah Manager", "hannah@xyzcompany.com", "manager", "HR Manager", "HR", False),
        ("Marcus Manager", "marcus@xyzcompany.com", "manager", "Marketing Manager", "Marketing", True),
        ("Sam Manager", "sam@xyzcompany.com", "manager", "Support Manager", "Support", True),
        # Staff
        ("Sarah Sales", "sarah@xyzcompany.com", "member", "Sales Executive", "Sales", False),
        ("Tom Ops", "tom@xyzcompany.com", "member", "Operations Associate", "Operations", False),
        ("Uma Finance", "uma@xyzcompany.com", "member", "Finance Associate", "Finance", False),
        ("Rachel HR", "rachel@xyzcompany.com", "member", "HR Associate", "HR", False),
        ("Mike Marketing", "mike@xyzcompany.com", "member", "Marketing Associate", "Marketing", False),
        ("Sonia Support", "sonia@xyzcompany.com", "member", "Support Agent", "Support", False),
        ("Penny Manager", "penny@xyzcompany.com", "manager", "Marketing Operations", "Marketing", False),
        ("Eve Viewer", "eve@xyzcompany.com", "member", "External Consultant", "Support", False),
    ]

    members = {}
    for name, email, role, designation, dept_name, is_head in members_data:
        member = OrgMember.query.filter_by(organization_id=org.id, email=email).first()
        if not member:
            member = OrgMember(
                organization_id=org.id, name=name, email=email, role=role,
                designation=designation, department_id=departments[dept_name].id,
                is_active=True, identity_id=f"sid_{secrets.token_hex(16)}",
                invited_by="founder@xyzcompany.com",
            )
            db.session.add(member)
            db.session.flush()
        members[email] = member

        # Set department head
        if is_head and dept_name in departments:
            dept = departments[dept_name]
            if not dept.head_identity_id:
                dept.head_identity_id = member.identity_id

    print(f"Members: {len(members)}")

    # 4. TeamMember accounts (for login)
    password_map = {}
    team_data = [
        ("ABC Founder", "founder@xyzcompany.com", "founder123", AuthUserRole.ADMIN.value),
        ("David Director", "david@xyzcompany.com", "director123", AuthUserRole.ADMIN.value),
        ("Olivia Director", "olivia@xyzcompany.com", "director123", AuthUserRole.ADMIN.value),
        ("Felicia Director", "felicia@xyzcompany.com", "director123", AuthUserRole.ADMIN.value),
        ("Henry Director", "henry@xyzcompany.com", "director123", AuthUserRole.ADMIN.value),
        ("Maya Manager", "maya@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Nathan Manager", "nathan@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Fiona Manager", "fiona@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Hannah Manager", "hannah@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Marcus Manager", "marcus@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Sam Manager", "sam@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Sarah Sales", "sarah@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
        ("Tom Ops", "tom@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
        ("Uma Finance", "uma@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
        ("Rachel HR", "rachel@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
        ("Mike Marketing", "mike@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
        ("Sonia Support", "sonia@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
        ("Penny Manager", "penny@xyzcompany.com", "manager123", AuthUserRole.MANAGER.value),
        ("Eve Viewer", "eve@xyzcompany.com", "staff123", AuthUserRole.AGENT.value),
    ]
    for name, email, pwd, role in team_data:
        tm = TeamMember.query.filter_by(email=email).first()
        if not tm:
            salt = secrets.token_hex(16)
            tm = TeamMember(
                name=name, email=email, role=role,
                password_hash=f"{salt}${hashlib.sha256((salt + pwd).encode()).hexdigest()}",
                is_active=True, api_token=secrets.token_hex(32),
            )
            db.session.add(tm)
        password_map[email] = pwd

    # 5. AuthZ roles
    role_perms = {
        "owner": ["org.view","org.edit","org.delete","org.manage_members","org.manage_billing","org.export_data",
            "rel.view","rel.create","rel.edit","rel.delete","rel.merge","rel.view_timeline","rel.edit_memory",
            "proposal.view","proposal.create","proposal.edit","proposal.delete","proposal.send","proposal.approve","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.edit","knowledge.delete","knowledge.search",
            "finance.view","finance.create_invoice","finance.edit_invoice","finance.record_payment","finance.reconcile","finance.view_reports",
            "task.view","task.create","task.edit","task.assign","task.complete",
            "ai.use","ai.edit_memory","ai.manage_prompts",
            "admin.view_audit","admin.manage_roles","admin.manage_industry_packs","admin.manage_integrations"],
        "admin": ["org.edit","org.manage_members","rel.view","rel.create","rel.edit","rel.merge","rel.view_timeline","rel.edit_memory",
            "proposal.view","proposal.create","proposal.edit","proposal.send","proposal.approve","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.edit","knowledge.search",
            "finance.view","finance.create_invoice","finance.edit_invoice","finance.record_payment","finance.view_reports",
            "task.view","task.create","task.edit","task.assign","task.complete","ai.use","ai.edit_memory","admin.view_audit"],
        "manager": ["rel.view","rel.create","rel.edit","rel.view_timeline",
            "proposal.view","proposal.create","proposal.edit","proposal.send","proposal.approve","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.search",
            "finance.view","finance.view_reports","task.view","task.create","task.edit","task.assign","task.complete","ai.use"],
        "member": ["rel.view","rel.create","rel.edit","rel.view_timeline",
            "proposal.view","proposal.create","proposal.edit","proposal.ai_generate",
            "knowledge.view","knowledge.upload","knowledge.search",
            "task.view","task.create","task.edit","ai.use"],
        "viewer": ["rel.view","rel.view_timeline","proposal.view","knowledge.view","knowledge.search","task.view"],
    }
    for role_name, perms in role_perms.items():
        existing = Role.query.filter_by(organization_id=org.id, name=role_name).first()
        if not existing:
            display_map = {"owner": "Owner", "admin": "Admin", "manager": "Manager", "member": "Member", "viewer": "Viewer"}
            desc_map = {"owner": "Full control", "admin": "Manage settings, members, data",
                "manager": "Operations, approvals", "member": "Create and edit own data", "viewer": "Read-only"}
            r = Role(organization_id=org.id, name=role_name,
                display_name=display_map[role_name], description=desc_map[role_name],
                permissions=json.dumps(perms), is_system=True)
            db.session.add(r)

    # 6. Assign OrgMemberRoles
    role_map = {r.name: r for r in Role.query.filter_by(organization_id=org.id).all()}
    assignments = 0
    for email, member in members.items():
        org_role = member.role
        if org_role in role_map and org_role != "viewer":
            existing = OrgMemberRole.query.filter_by(organization_id=org.id, member_id=member.id, role_id=role_map[org_role].id).first()
            if not existing:
                db.session.add(OrgMemberRole(organization_id=org.id, member_id=member.id, role_id=role_map[org_role].id, scope="organization", granted_by="system"))
                assignments += 1
        # Also assign viewer role to everyone
        if "viewer" in role_map:
            existing = OrgMemberRole.query.filter_by(organization_id=org.id, member_id=member.id, role_id=role_map["viewer"].id).first()
            if not existing:
                db.session.add(OrgMemberRole(organization_id=org.id, member_id=member.id, role_id=role_map["viewer"].id, scope="organization", granted_by="system"))

    db.session.commit()
    print(f"Role assignments: {assignments} new")
    print("\n=== SEEDING COMPLETE ===")
    print(f"Org: {Organization.query.get(org.id).name}")
    print(f"Depts: {Department.query.filter_by(organization_id=org.id).count()}")
    print(f"Members: {OrgMember.query.filter_by(organization_id=org.id).count()}")
    print(f"TeamMembers: {TeamMember.query.count()}")
    print(f"Roles: {Role.query.filter_by(organization_id=org.id).count()}")
    print(f"Assignments: {OrgMemberRole.query.filter_by(organization_id=org.id).count()}")

    # Print login credentials for all members
    print("\n--- Login Credentials ---")
    for email, pwd in password_map.items():
        print(f"  {email:35s} / {pwd:15s}")

    # Clean up sessions created by signin
    from app.founder.models import FounderSpace, FounderConversation, FounderMessage, FounderObject
    print(f"\nFounderSpaces: {FounderSpace.query.count()}")
    print(f"FounderObjects: {FounderObject.query.count()}")