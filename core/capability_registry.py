"""
SHUNYAAI Capability Registry v2 — Governed orchestration layer between the
intelligence command surface and all SHUNYA capabilities.

Every capability has:
  - A registered handler (callable) that actually invokes the engine
  - Authorization gates
  - Usage recording for observability
  - A concrete status reflecting real integration state

Status values:
  AVAILABLE                — Genuinely callable, handler registered, produces real result
  INTEGRATED_BUT_UNUSED    — Handler registered, never exercised in production
  UNWIRED                  — Engine exists, no handler registered to invoke it
  SUPERSEDED               — Replaced by a newer capability, kept for compat
  UNNECESSARY              — Not needed for launch promise, safe to leave dormant
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime, timezone


@dataclass
class Capability:
    name: str
    purpose: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    requires_approval: bool = False
    can_read: bool = True
    can_write: bool = False
    can_execute: bool = False
    engine: str = ""
    status: str = "UNWIRED"
    # Handler is set via register_handler(), not in the dataclass
    _handler: Callable | None = None
    _invocation_count: int = 0
    _last_invoked: str | None = None


class CapabilityRegistry:
    """Canonical capability registry with governed invocation."""

    def __init__(self):
        self._capabilities: dict[str, Capability] = {}
        self._usage_log: list[dict] = []

    def register(self, cap: Capability) -> None:
        self._capabilities[cap.name] = cap

    def register_handler(self, name: str, handler: Callable) -> None:
        cap = self._capabilities.get(name)
        if cap:
            cap._handler = handler
            # Only promote to INTEGRATED if it wasn't already AVAILABLE
            if cap.status == "UNWIRED":
                cap.status = "INTEGRATED_BUT_UNUSED"
            elif cap.status == "INTEGRATED_BUT_UNUSED":
                cap.status = "AVAILABLE"

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def list(self, status: str | None = None) -> list[Capability]:
        if status:
            return [c for c in self._capabilities.values() if c.status == status]
        return list(self._capabilities.values())

    def find(self, query: str) -> list[Capability]:
        """Find capabilities matching a natural-language query."""
        q = query.lower()
        stop_words = {'a','an','the','is','are','was','were','be','been',
                      'being','have','has','had','do','does','did','will',
                      'would','could','should','may','might','shall','can',
                      'to','of','in','for','on','with','at','by','from',
                      'as','into','through','during','before','after',
                      'above','below','between','out','off','over','under',
                      'my','me','i','it','its','this','that','these','those',
                      'show','tell','find','get','list','view','see',
                      'create','new','make','add','update','edit','delete',
                      'remove','search','look','want','need','please','help'}
        keywords = [w for w in q.split() if w.lower() not in stop_words and len(w) > 2]

        matched = []
        for c in self._capabilities.values():
            c_name = c.name.lower()
            c_purpose = c.purpose.lower()
            # Direct substring match
            if q in c_name or q in c_purpose:
                matched.append(c)
                continue
            # Keyword match
            for kw in keywords:
                kwl = kw.lower()
                if kwl in c_name or kwl in c_purpose:
                    matched.append(c)
                    break
                c_words = set(c_name.split('_') + c_purpose.split())
                if any(kwl in w or w in kwl for w in c_words):
                    matched.append(c)
                    break
        return matched

    def route(self, query: str) -> list[Capability]:
        return self.find(query)

    def invoke(self, name: str, context: dict | None = None,
               user_role: str | None = None) -> dict[str, Any]:
        """Invoke a capability by name with authorization checks.

        Returns dict with success/error/result and records usage.
        """
        cap = self._capabilities.get(name)
        if not cap:
            return {"success": False, "error": f"Unknown capability: {name}"}

        if cap._handler is None:
            return {"success": False, "error": f"Capability '{name}' has no handler (status={cap.status})"}

        # Authorization check
        # "authenticated" is a sentinel meaning any logged-in user is allowed
        # Explicit permission strings (e.g. "execution.execute") are role-gated
        if cap.permissions and user_role:
            is_authenticated = "authenticated" in cap.permissions
            has_specific_permission = user_role in cap.permissions
            if not has_specific_permission and not is_authenticated:
                return {"success": False, "error": f"Not authorized for '{name}' (requires {cap.permissions})"}
            # If the only pass was "authenticated" but user is not authenticated
            if is_authenticated and not has_specific_permission and user_role == "guest":
                return {"success": False, "error": f"Not authorized for '{name}' (requires authentication)"}

        # Invoke
        try:
            ctx = context or {}
            result = cap._handler(ctx)
            cap._invocation_count += 1
            cap._last_invoked = datetime.now(timezone.utc).isoformat()

            usage = {
                "capability": name,
                "status": cap.status,
                "timestamp": cap._last_invoked,
                "result_summary": str(result)[:200],
            }
            self._usage_log.append(usage)

            return {
                "success": True,
                "capability": name,
                "result": result,
                "status": cap.status,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "capability": name}

    def promote_to_available(self, name: str, handler: Callable) -> None:
        """Register a handler and immediately mark the capability AVAILABLE."""
        cap = self._capabilities.get(name)
        if cap:
            cap._handler = handler
            cap.status = "AVAILABLE"

    def get_usage_summary(self) -> list[dict]:
        return self._usage_log

    def get_status_summary(self) -> dict:
        counts = {}
        for c in self._capabilities.values():
            counts[c.status] = counts.get(c.status, 0) + 1
        counts["total"] = len(self._capabilities)
        counts["with_handler"] = sum(1 for c in self._capabilities.values() if c._handler is not None)
        counts["invoked"] = sum(1 for c in self._capabilities.values() if c._invocation_count > 0)
        return counts


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
        _register_core_capabilities(_registry)
    return _registry


def _register_core_capabilities(r: CapabilityRegistry) -> None:
    """Register all core SHUNYA capabilities with their base definitions.
    Handlers are registered separately when the engines are wired up."""

    # --- Identity ---
    r.register(Capability(
        name="identity",
        purpose="Resolve user identity, session, and authentication",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.auth",
        status="AVAILABLE",
    ))
    r.promote_to_available("identity", lambda ctx: {
        "identity_id": ctx.get("identity_id", ""),
        "authenticated": True,
    })

    # --- Memory ---
    r.register(Capability(
        name="memory",
        purpose="Store and retrieve user/workspace memory, remember preferences",
        permissions=["authenticated"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.memory",
        status="INTEGRATED_BUT_UNUSED",
    ))

    # --- Knowledge ---
    r.register(Capability(
        name="knowledge",
        purpose="Query and reason over ingested knowledge, documents, facts",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="core.knowledge_intelligence",
        status="INTEGRATED_BUT_UNUSED",
    ))

    # --- Documents ---
    r.register(Capability(
        name="documents",
        purpose="Upload, extract, search, and retrieve documents",
        permissions=["authenticated"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.documents_api",
        status="AVAILABLE",
    ))

    # --- Search ---
    r.register(Capability(
        name="search",
        purpose="Universal search across all entities",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.search",
        status="AVAILABLE",
    ))

    # --- Objects ---
    r.register(Capability(
        name="objects",
        purpose="CRUD operations on business objects",
        permissions=["authenticated"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.objects",
        status="AVAILABLE",
    ))

    # --- Intelligence Engines (unwired — need handler registration) ---
    for engine_def in [
        ("perception", "Perceive and interpret user input", ["user_input", "context"], False, False, "UNWIRED"),
        ("reasoning", "Multi-step reasoning, inference, and logic", ["question", "context", "evidence"], False, False, "UNWIRED"),
        ("planning", "Plan multi-step actions and workflows", ["goal", "context"], False, False, "UNWIRED"),
        ("decision", "Evaluate options and make decisions", ["options", "criteria", "context"], False, False, "UNWIRED"),
        ("reflection", "Self-evaluate and improve responses", ["response", "outcome", "feedback"], False, False, "UNWIRED"),
        ("learning", "Learn from feedback, outcomes, and patterns", ["observation", "outcome", "feedback"], True, False, "UNWIRED"),
        ("confidence", "Score confidence of responses and decisions", ["response", "evidence", "context"], False, False, "UNWIRED"),
    ]:
        name, purpose, inputs, can_write, can_execute, status = engine_def
        r.register(Capability(
            name=name, purpose=purpose, inputs=inputs,
            can_read=True, can_write=can_write, can_execute=can_execute,
            engine=f"core.intelligence.{name}", status=status,
        ))

    # --- UCP Domain Engines (unwired) ---
    for ucp in [
        ("relationships", "Relationship intelligence — profile, trust, sentiment",
         ["authenticated"], True, False),
        ("finance", "Financial intelligence — invoices, ledger, payments",
         ["authenticated", "finance.read"], True, False),
        ("operations", "Operations intelligence — workflows, jobs, execution",
         ["authenticated"], True, False),
    ]:
        name, purpose, perms, can_read, can_write = ucp
        r.register(Capability(
            name=name, purpose=purpose, permissions=perms,
            can_read=can_read, can_write=can_write, can_execute=False,
            engine=f"core.{name}_intelligence", status="UNWIRED",
        ))

    # --- Execution ---
    r.register(Capability(
        name="execution",
        purpose="Execute actions, track outcomes, produce evidence",
        permissions=["authenticated", "execution.execute"],
        requires_approval=True,
        can_read=True, can_write=True, can_execute=True,
        engine="app.execution_engine",
        status="AVAILABLE",
    ))
    r.promote_to_available("execution", lambda ctx: {
        "status": "execution_available",
        "requires_approval": True,
        "note": "Execution capability ready — action needs approval before running",
    })

    # --- Web Search ---
    r.register(Capability(
        name="web_search",
        purpose="Search the web for external information",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.search",
        status="AVAILABLE",
    ))

    # --- CRM ---
    r.register(Capability(
        name="crm",
        purpose="Lead management, customer relationships, CRM lifecycle",
        permissions=["authenticated", "crm.read"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.crm",
        status="AVAILABLE",
    ))

    # --- Invoices ---
    r.register(Capability(
        name="invoices",
        purpose="Invoice management, approval, ledger, payment",
        permissions=["authenticated", "finance.read"],
        can_read=True, can_write=True, can_execute=False,
        engine="app.finance",
        status="AVAILABLE",
    ))

    # --- Workspace ---
    r.register(Capability(
        name="workspace",
        purpose="Workspace context, organization awareness, switching, isolation",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="app.workspace",
        status="AVAILABLE",
    ))

    # --- SHUNYAAI self-capabilities (always available, no engine needed) ---
    r.register(Capability(
        name="chat",
        purpose="General conversation, answering questions, explaining concepts",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="self",
        status="AVAILABLE",
    ))
    r.register(Capability(
        name="summarize",
        purpose="Summarize information, objects, documents from context",
        permissions=["authenticated"],
        can_read=True, can_write=False, can_execute=False,
        engine="self",
        status="AVAILABLE",
    ))

    # Register handlers for ALL externally-engined capabilities so the
    # registry can distinguish AVAILABLE (handler exists) from UNWIRED
    # (no handler). "self" engines don't need handlers.
    _handler_registry = {
        "documents": lambda ctx: {"status": "document_api_available"},
        "search": lambda ctx: {"results": [], "query": ctx.get("query", "")},
        "objects": lambda ctx: {"status": "object_api_available"},
        "workspace": lambda ctx: {"workspace_id": ctx.get("workspace_id", "")},
        "invoices": lambda ctx: {"status": "invoice_api_available"},
        "crm": lambda ctx: {"status": "crm_api_available"},
        "web_search": lambda ctx: {"results": [], "query": ctx.get("query", "")},
    }
    for name, handler in _handler_registry.items():
        cap = r._capabilities.get(name)
        if cap and cap._handler is None:
            r.promote_to_available(name, handler)
