"""
Shunya — Universal Dashboard Configurator

Any business signs up, tells us what they are, and the dashboard
configures itself. AI adapts modules, fields, statuses, roles,
and layout to the business domain.

Architecture:
  BusinessType → Ontology → Module Config → Dashboard Layout
       ↑                                        |
       └── AI Assistant modifies at any time ───┘
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DashboardModule:
    """A single module/widget on the dashboard."""
    id: str
    label: str
    icon: str
    route: str = ""
    enabled: bool = True
    order: int = 0
    config: dict = field(default_factory=dict)


@dataclass
class BusinessOntology:
    """Complete dashboard configuration for a business type."""
    business_type: str
    label: str
    description: str = ""
    modules: list[DashboardModule] = field(default_factory=list)
    lead_statuses: list[str] = field(default_factory=list)
    team_roles: list[dict] = field(default_factory=list)
    default_fields: list[dict] = field(default_factory=list)
    dashboard_layout: str = "default"  # default, pipeline, calendar, analytics
    primary_metric: str = ""           # What matters most to this business
    onboarding_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "business_type": self.business_type,
            "label": self.label,
            "modules": [m.__dict__ for m in self.modules],
            "lead_statuses": self.lead_statuses,
            "team_roles": self.team_roles,
            "default_fields": self.default_fields,
            "dashboard_layout": self.dashboard_layout,
            "primary_metric": self.primary_metric,
        }


class OntologyRegistry:
    """Registry of all business ontologies. Extensible by design."""

    def __init__(self):
        self._ontologies: dict[str, BusinessOntology] = {}
        self._register_defaults()

    def get(self, business_type: str) -> Optional[BusinessOntology]:
        """Get ontology for a business type. Falls back to 'other'."""
        return self._ontologies.get(business_type, self._ontologies.get("other"))

    def list_types(self) -> list[dict]:
        return [{"id": k, "label": v.label, "icon": self._guess_icon(k)}
                for k, v in self._ontologies.items()]

    def register(self, ontology: BusinessOntology):
        self._ontologies[ontology.business_type] = ontology

    def _guess_icon(self, bt: str) -> str:
        icons = {"travel": "✈️", "hospital": "🏥", "school": "🎓", "retail": "🛍️",
                 "real_estate": "🏠", "hospitality": "🍽️", "legal": "⚖️",
                 "manufacturing": "🏭", "freelancer": "💼", "other": "📦",
                 "multi_brand": "🏢", "event": "🎪", "fitness": "💪",
                 "wellness": "🧘", "it_services": "💻", "ngo": "🤝",
                 "government": "🏛️", "agriculture": "🌾", "logistics": "🚚"}
        return icons.get(bt, "📦")

    def _register_defaults(self):
        """Register all built-in business ontologies."""

        self.register(BusinessOntology(
            business_type="travel",
            label="Travel & Tourism",
            description="Travel agencies, tour operators, destination management",
            modules=[
                DashboardModule("overview", "Overview", "🏠", "/", order=0),
                DashboardModule("pipeline", "Inquiries", "📋", "/leads?view=pipeline", order=1),
                DashboardModule("itineraries", "Itineraries", "🗺️", "/itineraries", order=2),
                DashboardModule("bookings", "Bookings", "🎫", "/bookings", order=3),
                DashboardModule("payments", "Payments", "💰", "/payments", order=4),
                DashboardModule("invoices", "Invoices", "🧾", "/invoices", order=5),
                DashboardModule("suppliers", "Suppliers", "🏢", "/suppliers", order=6),
                DashboardModule("calendar", "Calendar", "📅", "/calendar", order=7),
                DashboardModule("team", "Team", "👥", "/team", order=8),
                DashboardModule("reports", "Reports", "📈", "/reports", order=9),
                DashboardModule("relationships", "Relationships", "🤝", "/relationships", order=10),
                DashboardModule("hr", "HR", "👥", "/hr/dashboard", order=11),
                DashboardModule("notes", "Notes", "📝", "/notes", order=12),
                DashboardModule("support", "Support", "🎫", "/support/dashboard", order=13),
                DashboardModule("marketing", "Marketing", "🚀", "/marketing/dashboard", order=14),
                DashboardModule("sales", "Sales", "💎", "/sales/dashboard", order=15),
                DashboardModule("finance", "Finance", "💰", "/finance", order=16),
            ],
            lead_statuses=["new", "proposal", "negotiation", "booked", "completed", "cancelled"],
            team_roles=[{"id": "agent", "label": "Travel Agent"}, {"id": "manager", "label": "Team Lead"}, {"id": "admin", "label": "Director"}],
            default_fields=[
                {"name": "customer_name", "type": "text", "label": "Customer Name", "required": True},
                {"name": "destination", "type": "text", "label": "Destination"},
                {"name": "pax", "type": "number", "label": "Travelers"},
                {"name": "dates", "type": "text", "label": "Travel Dates"},
                {"name": "budget", "type": "number", "label": "Budget (₹)"},
                {"name": "phone", "type": "text", "label": "Phone"},
                {"name": "email", "type": "text", "label": "Email"},
            ],
            dashboard_layout="pipeline",
            primary_metric="Bookings",
            onboarding_questions=[
                "Do you handle outbound or inbound travel?",
                "How many agents are on your team?",
                "What destinations do you specialize in?",
            ],
        ))

        self.register(BusinessOntology(
            business_type="hospital",
            label="Healthcare & Hospitals",
            description="Clinics, hospitals, diagnostic centers, wellness clinics",
            modules=[
                DashboardModule("overview", "Overview", "🏠", "/", order=0),
                DashboardModule("patients", "Patients", "👤", "/patients", order=1),
                DashboardModule("appointments", "Appointments", "📅", "/appointments", order=2),
                DashboardModule("prescriptions", "Prescriptions", "💊", "/prescriptions", order=3),
                DashboardModule("billing", "Billing", "💰", "/billing", order=4),
                DashboardModule("inventory", "Inventory", "📦", "/inventory", order=5),
                DashboardModule("staff", "Staff", "👨‍⚕️", "/staff", order=6),
                DashboardModule("reports", "Reports", "📈", "/reports", order=7),
            ],
            lead_statuses=["new", "consultation", "diagnosis", "treatment", "follow_up", "recovered"],
            team_roles=[{"id": "doctor", "label": "Doctor"}, {"id": "nurse", "label": "Nurse"}, {"id": "reception", "label": "Receptionist"}, {"id": "admin", "label": "Admin"}],
            default_fields=[
                {"name": "patient_name", "type": "text", "label": "Patient Name", "required": True},
                {"name": "age", "type": "number", "label": "Age"},
                {"name": "blood_group", "type": "dropdown", "label": "Blood Group", "options": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]},
                {"name": "phone", "type": "text", "label": "Phone"},
                {"name": "symptoms", "type": "text", "label": "Symptoms"},
                {"name": "doctor_assigned", "type": "text", "label": "Doctor Assigned"},
            ],
            dashboard_layout="analytics",
            primary_metric="Patients Treated",
        ))

        self.register(BusinessOntology(
            business_type="school",
            label="Education & Schools",
            description="Schools, coaching centers, training institutes, universities",
            modules=[
                DashboardModule("overview", "Overview", "🏠", "/", order=0),
                DashboardModule("students", "Students", "👤", "/students", order=1),
                DashboardModule("classes", "Classes", "📚", "/classes", order=2),
                DashboardModule("attendance", "Attendance", "✅", "/attendance", order=3),
                DashboardModule("exams", "Exams", "📝", "/exams", order=4),
                DashboardModule("fees", "Fees", "💰", "/fees", order=5),
                DashboardModule("staff", "Staff", "👨‍🏫", "/staff", order=6),
                DashboardModule("timetable", "Timetable", "📅", "/timetable", order=7),
            ],
            lead_statuses=["inquiry", "application", "enrolled", "active", "graduated", "withdrawn"],
            team_roles=[{"id": "teacher", "label": "Teacher"}, {"id": "admin", "label": "Administrator"}, {"id": "accountant", "label": "Accountant"}],
            default_fields=[
                {"name": "student_name", "type": "text", "label": "Student Name", "required": True},
                {"name": "class", "type": "text", "label": "Class/Grade"},
                {"name": "parent_name", "type": "text", "label": "Parent Name"},
                {"name": "phone", "type": "text", "label": "Phone"},
                {"name": "address", "type": "text", "label": "Address"},
            ],
            dashboard_layout="analytics",
            primary_metric="Enrolled Students",
        ))

        self.register(BusinessOntology(
            business_type="retail",
            label="Retail & E-commerce",
            description="Stores, online shops, multi-brand retailers",
            modules=[
                DashboardModule("overview", "Overview", "🏠", "/", order=0),
                DashboardModule("orders", "Orders", "📦", "/orders", order=1),
                DashboardModule("products", "Products", "🛍️", "/products", order=2),
                DashboardModule("customers", "Customers", "👥", "/customers", order=3),
                DashboardModule("inventory", "Inventory", "📊", "/inventory", order=4),
                DashboardModule("payments", "Payments", "💰", "/payments", order=5),
                DashboardModule("suppliers", "Suppliers", "🏢", "/suppliers", order=6),
                DashboardModule("reports", "Reports", "📈", "/reports", order=7),
            ],
            lead_statuses=["lead", "quote", "order", "shipped", "delivered", "returned"],
            team_roles=[{"id": "sales", "label": "Sales Associate"}, {"id": "manager", "label": "Store Manager"}, {"id": "admin", "label": "Owner"}],
            default_fields=[
                {"name": "customer_name", "type": "text", "label": "Customer Name", "required": True},
                {"name": "product", "type": "text", "label": "Product"},
                {"name": "quantity", "type": "number", "label": "Quantity"},
                {"name": "amount", "type": "number", "label": "Amount (₹)"},
                {"name": "phone", "type": "text", "label": "Phone"},
            ],
            dashboard_layout="pipeline",
            primary_metric="Sales Revenue",
        ))

        # Register generic "other" fallback
        self.register(BusinessOntology(
            business_type="other",
            label="General Business",
            description="Any other business type — AI will adapt",
            modules=[
                DashboardModule("overview", "Overview", "🏠", "/", order=0),
                DashboardModule("leads", "Leads", "📋", "/leads?view=pipeline", order=1),
                DashboardModule("payments", "Payments", "💰", "/payments", order=2),
                DashboardModule("invoices", "Invoices", "🧾", "/invoices", order=3),
                DashboardModule("team", "Team", "👥", "/team", order=4),
                DashboardModule("reports", "Reports", "📈", "/reports", order=5),
            ],
            lead_statuses=["new", "active", "pending", "won", "lost"],
            team_roles=[{"id": "member", "label": "Team Member"}, {"id": "manager", "label": "Manager"}, {"id": "admin", "label": "Admin"}],
            default_fields=[
                {"name": "name", "type": "text", "label": "Name", "required": True},
                {"name": "phone", "type": "text", "label": "Phone"},
                {"name": "notes", "type": "text", "label": "Notes"},
            ],
            dashboard_layout="default",
            primary_metric="Active Deals",
        ))

        # Multi-brand parent
        self.register(BusinessOntology(
            business_type="multi_brand",
            label="Multi-Brand / Parent Account",
            description="Operate multiple businesses under one parent account",
            modules=[
                DashboardModule("overview", "Overview", "🏠", "/", order=0),
                DashboardModule("brands", "My Brands", "🏢", "/brands", order=1),
                DashboardModule("team", "Team", "👥", "/team", order=2),
                DashboardModule("reports", "Analytics", "📊", "/analytics", order=3),
            ],
            lead_statuses=[],
            team_roles=[{"id": "owner", "label": "Owner"}, {"id": "manager", "label": "Brand Manager"}, {"id": "admin", "label": "Super Admin"}],
            dashboard_layout="analytics",
            primary_metric="Cross-Brand Revenue",
        ))


# Singleton
registry = OntologyRegistry()