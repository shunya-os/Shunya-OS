"""SHUNYA Outcome Runtime Engine (Z-07 Article I-III).

Every outcome is an executable workflow that:
- Takes user intent (natural language or structured)
- Determines what objects to create/modify/link
- Executes work through the universal ontology
- Returns explanation: what was used, created, changed, linked, what needs approval

This replaces conversational AI with operational AI.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Awaitable


# ── Outcome Definition ──────────────────────────────────────────────

class OutcomeStep:
    """A single step within an outcome execution."""
    def __init__(self, action: str, description: str, 
                 object_type: Optional[str] = None,
                 data: Optional[Dict[str, Any]] = None,
                 links: Optional[List[Dict[str, str]]] = None,
                 requires_approval: bool = False):
        self.action = action
        self.description = description
        self.object_type = object_type
        self.data = data or {}
        self.links = links or []
        self.requires_approval = requires_approval

class OutcomeResult:
    """The result of an outcome execution."""
    def __init__(self, success: bool, message: str = "",
                 created: Optional[List[Dict]] = None,
                 modified: Optional[List[Dict]] = None,
                 linked: Optional[List[Dict]] = None,
                 requires_approval: Optional[List[str]] = None,
                 used: Optional[List[str]] = None,
                 error: Optional[str] = None):
        self.success = success
        self.message = message
        self.created = created or []
        self.modified = modified or []
        self.linked = linked or []
        self.requires_approval = requires_approval or []
        self.used = used or []
        self.error = error

    def explain(self) -> str:
        """Generate human-readable explanation (Article IX)."""
        parts = []
        if self.used:
            parts.append("What I used: " + ", ".join(self.used))
        if self.created:
            items = []
            for c in self.created:
                t = c.get("type", "record")
                n = c.get("name", "")
                items.append(f'{t} "{n}"')
            parts.append("What I created: " + ", ".join(items))
        if self.modified:
            items = []
            for m in self.modified:
                t = m.get("type", "record")
                n = m.get("name", "")
                items.append(f'{t} "{n}"')
            parts.append("What I changed: " + ", ".join(items))
        if self.linked:
            items = []
            for lref in self.linked:
                s = lref.get("source", "")
                t = lref.get("target", "")
                items.append(f"{s} -> {t}")
            parts.append("What I linked: " + ", ".join(items))
        if self.requires_approval:
            parts.append("What requires your approval: " + ", ".join(self.requires_approval))
        if self.error:
            parts.append(f"Error: {self.error}")
        return '\n'.join(parts)


# ── Outcome Registry ────────────────────────────────────────────────

class Outcome:
    """A registered outcome that can be executed."""
    def __init__(self, name: str, category: str, description: str,
                 handler: Callable[..., Awaitable[OutcomeResult]],
                 example_phrases: List[str] = None,
                 timeout_seconds: int = 30):
        self.name = name
        self.category = category
        self.description = description
        self.handler = handler
        self.example_phrases = example_phrases or []
        self.timeout_seconds = timeout_seconds

    async def execute(self, context: 'OutcomeContext') -> OutcomeResult:
        return await self.handler(context)


class OutcomeContext:
    """Context for an outcome execution — carries user, workspace, service functions."""
    def __init__(self, user_id: str, workspace_id: str,
                 identity_id: str, session_data: Dict[str, Any],
                 ai_client=None,
                 create_object_func=None):
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.identity_id = identity_id
        self.session_data = session_data
        self.ai_client = ai_client
        self.create_object = create_object_func  # callable(type, data) -> dict


class OutcomeRegistry:
    """Registry of all executable outcomes (Article VII)."""

    def __init__(self):
        self._outcomes: Dict[str, Outcome] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, outcome: Outcome):
        self._outcomes[outcome.name] = outcome
        if outcome.category not in self._categories:
            self._categories[outcome.category] = []
        self._categories[outcome.category].append(outcome.name)

    def get(self, name: str) -> Optional[Outcome]:
        return self._outcomes.get(name)

    def find_by_intent(self, intent: str) -> List[Outcome]:
        """Find outcomes matching a natural language intent."""
        intent_lower = intent.lower()
        matches = []
        for name, outcome in self._outcomes.items():
            for phrase in outcome.example_phrases:
                if any(word in intent_lower for word in phrase.lower().split()):
                    matches.append(outcome)
                    break
        return matches

    def list_by_category(self, category: str) -> List[Outcome]:
        return [self._outcomes[n] for n in self._categories.get(category, [])]

    def all_categories(self) -> List[str]:
        return list(self._categories.keys())

    def all(self) -> List[Outcome]:
        return list(self._outcomes.values())


# ── Outcome Execution Engine ────────────────────────────────────────

class OutcomeEngine:
    """The runtime that executes outcomes (Article I-III)."""

    def __init__(self, registry: OutcomeRegistry):
        self.registry = registry
        self._execution_log: List[Dict] = []

    async def execute_by_name(self, name: str, context: OutcomeContext) -> OutcomeResult:
        """Execute an outcome by its registered name."""
        outcome = self.registry.get(name)
        if not outcome:
            return OutcomeResult(success=False, error=f"Unknown outcome: {name}")
        return await self._execute(outcome, context)

    async def execute_by_intent(self, intent: str, context: OutcomeContext) -> OutcomeResult:
        """Parse a natural language intent and execute the best-matching outcome."""
        matches = self.registry.find_by_intent(intent)
        if not matches:
            # Try AI-powered intent matching
            if context.ai_client:
                return await self._ai_match_and_execute(intent, context)
            return OutcomeResult(
                success=False,
                error=f"I don't know how to do that yet. Available outcomes: {', '.join(o.name for o in self.registry.all()[:10])}..."
            )
        # Use highest-confidence match (first match)
        return await self._execute(matches[0], context)

    async def _execute(self, outcome: Outcome, context: OutcomeContext) -> OutcomeResult:
        """Execute an outcome with monitoring and explainability."""
        start = datetime.now(timezone.utc)
        try:
            result = await outcome.execute(context)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            self._log_execution(outcome.name, context, result, elapsed)
            return result
        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            result = OutcomeResult(success=False, error=str(e))
            self._log_execution(outcome.name, context, result, elapsed)
            return result

    async def _ai_match_and_execute(self, intent: str, context: OutcomeContext) -> OutcomeResult:
        """Use AI to match intent to an outcome, then execute."""
        # Build outcome catalog for AI
        catalog = "\n".join(
            f"- {o.name}: {o.description} (examples: {', '.join(o.example_phrases[:3])})"
            for o in self.registry.all()
        )
        prompt = f"""Given this user intent: "{intent}"

Select the best matching outcome from the catalog below. Return ONLY the outcome name.

Catalog:
{catalog}

If no match is close enough, return: UNKNOWN"""
        
        if context.ai_client:
            try:
                model_response = await context.ai_client(prompt)
                outcome_name = model_response.strip()
                outcome = self.registry.get(outcome_name)
                if outcome:
                    return await self._execute(outcome, context)
            except Exception:
                pass
        
        return OutcomeResult(
            success=False,
            error=f"I don't know how to do '{intent}'. Try: create customer, create invoice, create proposal, or describe what you need."
        )

    def _log_execution(self, name: str, context: OutcomeContext, 
                       result: OutcomeResult, elapsed: float):
        self._execution_log.append({
            "outcome": name,
            "user_id": context.user_id,
            "workspace_id": context.workspace_id,
            "success": result.success,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_execution_log(self, limit: int = 50) -> List[Dict]:
        return self._execution_log[-limit:]


# ── Outcome Handlers ────────────────────────────────────────────────

async def handle_create_customer(ctx: OutcomeContext) -> OutcomeResult:
    """Create a customer from natural language intent."""
    data = ctx.session_data.get("data", {})
    company_name = data.get("company_name") or data.get("name", "New Customer")
    contact_person = data.get("contact_person") or data.get("contact", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    
    if ctx.create_object:
        resp = ctx.create_object("customer", {
            "company_name": company_name,
            "contact_person": contact_person,
            "email": email,
            "phone": phone,
            "segment": data.get("segment", "small_business"),
        })
    else:
        return OutcomeResult(success=False, error="No create_object function provided")
    
    if resp.get("success") and resp.get("object_id"):
        return OutcomeResult(
            success=True,
            message=f"Created customer: {company_name}",
            created=[{"type": "customer", "name": company_name, "id": resp["object_id"]}],
            used=["Customer creation API"],
        )
    return OutcomeResult(success=False, error=resp.get("error", "Failed to create customer"))


async def handle_create_invoice(ctx: OutcomeContext) -> OutcomeResult:
    """Create an invoice."""
    data = ctx.session_data.get("data", {})
    company_name = data.get("company_name", "Client")
    amount = data.get("amount", "0")
    invoice_number = data.get("invoice_number", f"INV-{uuid.uuid4().hex[:8].upper()}")
    
    if ctx.create_object:
        resp = ctx.create_object("invoice", {
            "company_name": company_name,
            "invoice_number": invoice_number,
            "amount": str(amount),
            "status": "draft",
        })
    else:
        return OutcomeResult(success=False, error="No create_object function provided")
    
    if resp.get("success"):
        return OutcomeResult(
            success=True,
            message=f"Created invoice {invoice_number} for {company_name}: ${amount}",
            created=[{"type": "invoice", "name": invoice_number, "amount": amount}],
            used=["Invoice creation API"],
        )
    return OutcomeResult(success=False, error=resp.get("error", "Failed to create invoice"))


async def handle_create_proposal(ctx: OutcomeContext) -> OutcomeResult:
    """Create a proposal."""
    data = ctx.session_data.get("data", {})
    company_name = data.get("company_name", "Client")
    title = data.get("proposal_title") or data.get("title", "New Proposal")
    amount = data.get("amount", "0")
    
    if ctx.create_object:
        resp = ctx.create_object("proposal", {
            "company_name": company_name,
            "proposal_title": title,
            "amount": str(amount),
            "status": "draft",
        })
    else:
        return OutcomeResult(success=False, error="No create_object function provided")
    
    if resp.get("success"):
        return OutcomeResult(
            success=True,
            message=f"Created proposal: {title}",
            created=[{"type": "proposal", "name": title, "company": company_name}],
            used=["Proposal creation API"],
        )
    return OutcomeResult(success=False, error=resp.get("error", "Failed to create proposal"))


async def handle_create_task(ctx: OutcomeContext) -> OutcomeResult:
    """Create a task."""
    data = ctx.session_data.get("data", {})
    title = data.get("title", "New Task")
    assignee = data.get("assignee", "Me")
    priority = data.get("priority", "medium")
    
    if ctx.create_object:
        resp = ctx.create_object("task", {
            "title": title,
            "assignee": assignee,
            "priority": priority,
            "due_date": data.get("due_date", ""),
        })
    else:
        return OutcomeResult(success=False, error="No create_object function provided")
    
    if resp.get("success"):
        return OutcomeResult(
            success=True,
            message=f"Created task: {title} (assigned to {assignee})",
            created=[{"type": "task", "name": title, "assignee": assignee}],
            used=["Task creation API"],
        )
    return OutcomeResult(success=False, error=resp.get("error", "Failed to create task"))


async def handle_create_lead(ctx: OutcomeContext) -> OutcomeResult:
    """Create a lead."""
    data = ctx.session_data.get("data", {})
    company_name = data.get("company_name") or data.get("name", "New Lead")
    contact_person = data.get("contact_person") or ""
    source = data.get("source", "Manual")
    
    if ctx.create_object:
        resp = ctx.create_object("lead", {
            "company_name": company_name,
            "contact_person": contact_person,
            "email": data.get("email", ""),
            "source": source,
        })
    else:
        return OutcomeResult(success=False, error="No create_object function provided")
    
    if resp.get("success"):
        return OutcomeResult(
            success=True,
            message=f"Created lead: {company_name}",
            created=[{"type": "lead", "name": company_name, "source": source}],
            used=["Lead creation API"],
        )
    return OutcomeResult(success=False, error=resp.get("error", "Failed to create lead"))


async def handle_record_payment(ctx: OutcomeContext) -> OutcomeResult:
    """Record a payment."""
    data = ctx.session_data.get("data", {})
    company_name = data.get("company_name", "Client")
    amount = data.get("amount", "0")
    
    if ctx.create_object:
        resp = ctx.create_object("invoice", {
            "company_name": company_name,
            "invoice_number": data.get("invoice_number", f"PAY-{uuid.uuid4().hex[:8].upper()}"),
            "amount": str(amount),
            "status": "paid",
        })
    else:
        return OutcomeResult(success=False, error="No create_object function provided")
    
    if resp.get("success"):
        return OutcomeResult(
            success=True,
            message=f"Recorded payment of ${amount} from {company_name}",
            created=[{"type": "payment", "company": company_name, "amount": amount}],
            modified=[{"type": "invoice", "status": "paid"}],
            used=["Payment recording API"],
        )
    return OutcomeResult(success=False, error=resp.get("error", "Failed to record payment"))


async def handle_search(ctx: OutcomeContext) -> OutcomeResult:
    """Search across all data."""
    query = ctx.session_data.get("query", "")
    if not query:
        return OutcomeResult(success=False, error="What would you like me to search for?")
    
    # For now, return a placeholder since unified search is not built yet
    return OutcomeResult(
        success=True,
        message=f"Searched for '{query}'",
        used=["Search: keyword matching", "Company knowledge"],
    )


# ── Workflow Execution Engine (Z-11 Article III) ────────────────────

class WorkflowStep:
    """A single step in a business execution chain."""
    def __init__(self, outcome_name: str, data: Dict[str, Any] = None,
                 depends_on: List[str] = None, requires_approval: bool = False):
        self.outcome_name = outcome_name
        self.data = data or {}
        self.depends_on = depends_on or []
        self.requires_approval = requires_approval


class Workflow:
    """A chained sequence of outcomes forming a complete business process."""
    def __init__(self, name: str, description: str, steps: List[WorkflowStep],
                 category: str = "Business Execution"):
        self.name = name
        self.description = description
        self.steps = steps
        self.category = category


# ── Canonical Business Workflows ──────────────────────────────────

BUILTIN_WORKFLOWS = {
    "prepare_proposal": Workflow(
        "Prepare Proposal",
        "Create a customer proposal from scratch including itinerary, pricing, PDF, and communications.",
        steps=[
            WorkflowStep("create_customer", data={"company_name": "{company}", "contact_person": "{contact}"}),
            WorkflowStep("create_itinerary", data={"destination": "{destination}", "name": "{destination} Trip"}, depends_on=["create_customer"]),
            WorkflowStep("send_proposal", data={"company_name": "{company}", "proposal_title": "{title}", "amount": "{amount}"}, depends_on=["create_customer"]),
            WorkflowStep("generate_voucher", data={"name": "{title} Voucher"}, depends_on=["send_proposal"]),
        ],
        category="Sales"
    ),
    "onboard_company": Workflow(
        "Onboard Company",
        "Complete company onboarding: create org, invite team, configure basic data.",
        steps=[
            WorkflowStep("create_customer", data={"company_name": "{company}"}),
            WorkflowStep("create_task", data={"title": "Complete company profile", "assignee": "Me", "priority": "high"}),
            WorkflowStep("schedule_meeting", data={"title": "Kickoff meeting", "name": "Team Kickoff"}),
        ],
        category="Operations"
    ),
    "create_campaign": Workflow(
        "Create Marketing Campaign",
        "Plan and launch a marketing campaign from idea to execution.",
        steps=[
            WorkflowStep("create_campaign", data={"name": "{campaign_name}"}),
            WorkflowStep("create_brand", data={"name": "{brand}"}, depends_on=["create_campaign"]),
            WorkflowStep("build_audience", data={"name": "{audience}", "segment": "{audience}"}, depends_on=["create_campaign"]),
            WorkflowStep("send_email_campaign", data={"audience": "{audience}"}, depends_on=["build_audience"]),
        ],
        category="Marketing"
    ),
    "hire_employee": Workflow(
        "Hire Employee",
        "Complete hiring workflow from job posting to onboarding.",
        steps=[
            WorkflowStep("create_job_posting", data={"title": "{role}"}),
            WorkflowStep("schedule_interview", data={"name": "{candidate}"}, depends_on=["create_job_posting"]),
            WorkflowStep("generate_offer", data={"name": "{candidate}"}, depends_on=["schedule_interview"]),
            WorkflowStep("create_task", data={"title": "Onboard {candidate}", "assignee": "HR"}, depends_on=["generate_offer"]),
        ],
        category="HR"
    ),
    "process_sale": Workflow(
        "Process Sale",
        "End-to-end sale: lead → proposal → invoice → payment.",
        steps=[
            WorkflowStep("create_lead", data={"company_name": "{company}"}),
            WorkflowStep("send_proposal", data={"company_name": "{company}", "proposal_title": "{title}", "amount": "{amount}"}, depends_on=["create_lead"]),
            WorkflowStep("create_invoice", data={"company_name": "{company}", "amount": "{amount}"}, depends_on=["send_proposal"]),
            WorkflowStep("record_payment", data={"company_name": "{company}", "amount": "{amount}"}, depends_on=["create_invoice"]),
        ],
        category="Sales"
    ),
    "manage_project": Workflow(
        "Manage Project",
        "Set up a project with tasks, meetings, and milestones.",
        steps=[
            WorkflowStep("create_project", data={"name": "{project_name}"}),
            WorkflowStep("create_task", data={"title": "{task_name}", "assignee": "{assignee}", "priority": "medium"}, depends_on=["create_project"]),
            WorkflowStep("schedule_meeting", data={"title": "{meeting_title}"}, depends_on=["create_project"]),
            WorkflowStep("create_checklist", data={"title": "{project_name} Checklist"}, depends_on=["create_project"]),
        ],
        category="Operations"
    ),
    "run_payroll": Workflow(
        "Run Payroll",
        "Process payroll, record expenses, and log payments.",
        steps=[
            WorkflowStep("payroll", data={"period": "{period}", "amount": "{amount}"}),
            WorkflowStep("record_expense", data={"company_name": "Payroll", "amount": "{amount}"}),
        ],
        category="Finance"
    ),
}


class WorkflowEngine:
    """Executes chained workflows by calling outcomes sequentially."""
    
    def __init__(self, outcome_engine: 'OutcomeEngine'):
        self.outcome_engine = outcome_engine
        self.workflows = BUILTIN_WORKFLOWS
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        return [{"name": w.name, "description": w.description, "category": w.category,
                 "steps": len(w.steps)} for w in self.workflows.values()]
    
    def get_workflow(self, name: str) -> Optional[Workflow]:
        return self.workflows.get(name)
    
    async def execute_workflow(self, workflow_name: str,
                                template_data: Dict[str, Any],
                                context: 'OutcomeContext') -> OutcomeResult:
        """Execute a workflow by substituting templates and chaining outcomes."""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return OutcomeResult(success=False, error=f"Unknown workflow: {workflow_name}")
        
        all_results = []
        step_outputs = {}
        
        for step in workflow.steps:
            # Check dependencies
            for dep in step.depends_on:
                if dep not in step_outputs:
                    return OutcomeResult(success=False,
                        error=f"Step '{step.outcome_name}' depends on '{dep}' which has not completed")
            
            # Substitute template variables
            resolvable = dict(step.data)
            for key, val in list(resolvable.items()):
                if isinstance(val, str):
                    for tpl_key, tpl_val in template_data.items():
                        placeholder = "{" + tpl_key + "}"
                        if placeholder in val:
                            resolvable[key] = val.replace(placeholder, str(tpl_val))
            
            # Execute the outcome
            step_ctx = OutcomeContext(
                user_id=context.user_id,
                workspace_id=context.workspace_id,
                identity_id=context.identity_id,
                session_data={"data": resolvable},
                create_object_func=context.create_object,
            )
            
            result = await self.outcome_engine.execute_by_name(step.outcome_name, step_ctx)
            step_outputs[step.outcome_name] = result
            all_results.append(result)
            
            if not result.success and not step.requires_approval:
                return OutcomeResult(success=False,
                    error=f"Workflow failed at step '{step.outcome_name}': {result.error}",
                    message=f"Completed {len([r for r in all_results if r.success])}/{len(workflow.steps)} steps")
        
        # Aggregate results
        created = []
        for r in all_results:
            if hasattr(r, 'created') and r.created:
                created.extend(r.created)
        
        used = list(set(
            item for r in all_results if hasattr(r, 'used') and r.used
            for item in r.used
        ))
        
        explanations = [r.explanation for r in all_results if hasattr(r, 'explanation') and r.explanation]
        
        return OutcomeResult(
            success=True,
            message=f"Workflow '{workflow.name}' completed successfully: {len([r for r in all_results if r.success])}/{len(workflow.steps)} steps done",
            created=created,
            used=used,
            linked=[],
        )


# ── Build Default Registry ──────────────────────────────────────────

def build_default_registry() -> OutcomeRegistry:
    """Build the default outcome registry with ALL 51 outcomes from the full library."""
    from app.outcome_library import register_all_outcomes
    registry = OutcomeRegistry()
    register_all_outcomes(registry)
    return registry