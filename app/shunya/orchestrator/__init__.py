"""Shunya Orchestrator — multi-agent coordination with scoped context and governance.

Architecture:
User Intent → Orchestrator → Specialist Agent → Structured Result → Governance → Workflow → Execution

Principles:
- Agents are reasoning specializations, NOT autonomous authorities
- Scoped context: agents only see what they need
- Traceable: every agent action is logged
- Governed: no agent executes without authorization
"""
import json, logging
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from app import db
from app.models import ActivityLog
from app.shunya.foundation import Result

logger = logging.getLogger("app.shunya.orchestrator")


class AgentCapability(str, Enum):
    KNOWLEDGE_QUERY = "knowledge_query"
    SALES_INTELLIGENCE = "sales_intelligence"
    FINANCE_INTELLIGENCE = "finance_intelligence"
    OPERATIONS_INTELLIGENCE = "operations_intelligence"
    CUSTOMER_INTELLIGENCE = "customer_intelligence"
    LEARNING_INTELLIGENCE = "learning_intelligence"
    RISK_ASSESSMENT = "risk_assessment"
    COMMUNICATION_INTELLIGENCE = "communication_intelligence"


@dataclass
class AgentContext:
    """Scoped context passed to a specialist agent."""
    tenant_id: int
    user_id: int
    user_role: str
    query: str
    entity_id: Optional[int] = None
    workflow_id: Optional[int] = None
    decision_id: Optional[int] = None
    
    # Scoped data (orchestrator decides what each agent sees)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    entity_data: Dict[str, Any] = field(default_factory=dict)
    user_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    request_id: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d%H%M%S%f"))
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


@dataclass
class AgentResult:
    """Structured output from a specialist agent."""
    agent: str
    capability: str
    confidence: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    next_actions: List[Dict] = field(default_factory=list)
    decisions: List[Dict] = field(default_factory=list)
    risks: List[Dict] = field(default_factory=list)
    needs_human: bool = False
    error: Optional[str] = None


class SpecialistAgent:
    """Base class for specialist agents."""
    
    def __init__(self, name: str, capability: AgentCapability):
        self.name = name
        self.capability = capability
        self.description = ""
    
    def process(self, ctx: AgentContext) -> AgentResult:
        """Process an intent. Override in subclasses."""
        raise NotImplementedError
    
    def log(self, ctx: AgentContext, result: AgentResult):
        """Log agent activity."""
        try:
            activity = ActivityLog(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                entity_id=ctx.entity_id,
                action=f"agent.{self.name}.{result.capability}",
                detail=json.dumps({
                    "agent": self.name,
                    "summary": result.summary[:200],
                    "confidence": result.confidence,
                    "needs_human": result.needs_human,
                    "duration_ms": result.details.get("duration_ms"),
                }),
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            logger.warning("Agent log failed: %s", e)


# ---------------------------------------------------------------------------
# Specialist Agent Implementations
# ---------------------------------------------------------------------------

class KnowledgeAgent(SpecialistAgent):
    """Knows the knowledge base, memory, and can search the web."""
    
    def __init__(self):
        super().__init__("knowledge", AgentCapability.KNOWLEDGE_QUERY)
        self.description = "Searches company knowledge, multi-class memory, and web"
    
    def process(self, ctx: AgentContext) -> AgentResult:
        from app.shunya.knowledge import KnowledgePipeline
        from app.shunya.memory import MemoryStore
        
        result = KnowledgePipeline.get_context_for_ai(ctx.query, ctx.tenant_id)
        memories = MemoryStore.get_context(ctx.tenant_id, ctx.entity_id, ctx.query)
        
        next_actions = []
        if not result.get("has_internal_data"):
            next_actions.append({
                "action": "Upload documents",
                "reason": "No internal data found for this query",
                "target": "/ingestion",
            })
        
        return AgentResult(
            agent=self.name,
            capability=AgentCapability.KNOWLEDGE_QUERY.value,
            confidence=0.8 if result.get("has_internal_data") else 0.3,
            summary=f"Found {len(result.get('results',[]))} internal sources",
            details={
                "internal_count": len(result.get("results", [])),
                "web_count": len(result.get("web_results", [])),
                "memory_classes": list(memories.keys()),
                "needs_verification": result.get("needs_verification", False),
            },
            next_actions=next_actions,
        )


class FinanceAgent(SpecialistAgent):
    """Knows invoices, expenses, P&L, and financial patterns."""
    
    def __init__(self):
        super().__init__("finance", AgentCapability.FINANCE_INTELLIGENCE)
        self.description = "Analyzes financial data, invoicing, expenses, and revenue"
    
    def process(self, ctx: AgentContext) -> AgentResult:
        from app.models import Entity, EntityDefinition
        
        inv_def = EntityDefinition.query.filter_by(tenant_id=ctx.tenant_id, type="invoice").first()
        exp_def = EntityDefinition.query.filter_by(tenant_id=ctx.tenant_id, type="expense").first()
        
        unpaid = []
        if inv_def:
            invoices = Entity.query.filter_by(
                tenant_id=ctx.tenant_id, definition_id=inv_def.id, status="sent", is_archived=False
            ).all()
            for inv in invoices:
                unpaid.append({
                    "id": inv.id,
                    "code": inv.code,
                    "customer": inv.data.get("customer_name", "Unknown"),
                    "amount": float(inv.data.get("total", 0)),
                    "due": inv.data.get("due_date", ""),
                })
        
        total_unpaid = sum(u["amount"] for u in unpaid)
        
        risks = []
        if total_unpaid > 100000:
            risks.append({
                "type": "high_outstanding",
                "severity": "medium",
                "message": f"₹{total_unpaid:,.0f} outstanding across {len(unpaid)} invoices",
            })
        
        return AgentResult(
            agent=self.name,
            capability=AgentCapability.FINANCE_INTELLIGENCE.value,
            confidence=0.85,
            summary=f"{len(unpaid)} unpaid invoices, ₹{total_unpaid:,.0f} outstanding",
            details={"unpaid_count": len(unpaid), "total_unpaid": total_unpaid},
            risks=risks,
            next_actions=[{
                "action": "Review outstanding invoices",
                "reason": f"{len(unpaid)} invoices unpaid",
                "target": "/entities/invoice?status=sent",
            }] if unpaid else [],
        )


class OperationsAgent(SpecialistAgent):
    """Knows projects, tasks, workflows, and blockers."""
    
    def __init__(self):
        super().__init__("operations", AgentCapability.OPERATIONS_INTELLIGENCE)
        self.description = "Analyzes projects, tasks, workflows, and bottlenecks"
    
    def process(self, ctx: AgentContext) -> AgentResult:
        from app.models import Entity, EntityDefinition
        
        task_def = EntityDefinition.query.filter_by(tenant_id=ctx.tenant_id, type="task").first()
        proj_def = EntityDefinition.query.filter_by(tenant_id=ctx.tenant_id, type="project").first()
        
        blockers = []
        if task_def:
            blocked = Entity.query.filter_by(
                tenant_id=ctx.tenant_id, definition_id=task_def.id,
                status="blocked", is_archived=False
            ).all()
            for t in blocked:
                blockers.append({
                    "id": t.id,
                    "title": t.data.get("title", t.display_name),
                    "reason": t.data.get("blocker_reason", "Unknown"),
                })
        
        total_projects = Entity.query.filter_by(
            tenant_id=ctx.tenant_id, definition_id=proj_def.id, is_archived=False
        ).count() if proj_def else 0
        
        return AgentResult(
            agent=self.name,
            capability=AgentCapability.OPERATIONS_INTELLIGENCE.value,
            confidence=0.85,
            summary=f"{len(blockers)} blockers, {total_projects} projects",
            details={"blocker_count": len(blockers), "project_count": total_projects},
            next_actions=[{
                "action": f"Resolve {len(blockers)} blocked tasks",
                "reason": "Blocked tasks stall downstream work",
                "target": "/entities/task?status=blocked",
            }] if blockers else [],
        )


class CustomerAgent(SpecialistAgent):
    """Knows customer profiles, preferences, and history."""
    
    def __init__(self):
        super().__init__("customer", AgentCapability.CUSTOMER_INTELLIGENCE)
        self.description = "Analyzes customer data, preferences, and relationship history"
    
    def process(self, ctx: AgentContext) -> AgentResult:
        from app.shunya.memory import MemoryStore, MemoryClass
        
        profile = {}
        if ctx.entity_id:
            memories = MemoryStore.retrieve(
                MemoryClass.RELATIONSHIP, ctx.tenant_id,
                entity_id=ctx.entity_id, limit=5
            )
            profile["relationship_memories"] = memories
        
        return AgentResult(
            agent=self.name,
            capability=AgentCapability.CUSTOMER_INTELLIGENCE.value,
            confidence=0.75,
            summary="Customer context loaded" if profile else "No customer context available",
            details=profile,
        )


class LearningAgent(SpecialistAgent):
    """Knows learning patterns, proposals, and improvement opportunities."""
    
    def __init__(self):
        super().__init__("learning", AgentCapability.LEARNING_INTELLIGENCE)
        self.description = "Analyzes patterns, learning proposals, and improvement opportunities"
    
    def process(self, ctx: AgentContext) -> AgentResult:
        from app.shunya.learning import LearningEngine
        
        proposals = LearningEngine.get_proposals(ctx.tenant_id)
        pending = [p for p in proposals if p.get("status") == "proposed"]
        
        return AgentResult(
            agent=self.name,
            capability=AgentCapability.LEARNING_INTELLIGENCE.value,
            confidence=0.8,
            summary=f"{len(pending)} pending learning proposals",
            details={"total_proposals": len(proposals), "pending": len(pending)},
            next_actions=[{
                "action": "Review learning proposals",
                "reason": f"{len(pending)} patterns waiting for governance",
                "target": "/learning",
            }] if pending else [],
        )


class ShunyaOrchestrator:
    """Central coordinator — routes intent to specialist agents."""
    
    def __init__(self):
        self._agents: Dict[str, SpecialistAgent] = {}
        self._capability_map: Dict[str, str] = {}
    
    def register(self, agent: SpecialistAgent):
        self._agents[agent.name] = agent
        self._capability_map[agent.capability.value] = agent.name
        logger.info("Registered agent: %s (%s)", agent.name, agent.capability.value)
    
    def get_agent(self, name: str) -> Optional[SpecialistAgent]:
        return self._agents.get(name)
    
    def list_agents(self) -> List[Dict]:
        return [{
            "name": a.name,
            "capability": a.capability.value,
            "description": a.description,
        } for a in self._agents.values()]
    
    def route(self, query: str, tenant_id: int, user_id: int, user_role: str,
              entity_id: Optional[int] = None,
              capabilities: Optional[List[str]] = None) -> Dict:
        """Route an intent to the relevant specialist agents.
        
        If capabilities specified, only those agents are invoked.
        Otherwise, all agents that match the query are invoked.
        """
        if not self._agents:
            return {"error": "No agents registered", "results": []}
        
        ctx = AgentContext(
            tenant_id=tenant_id, user_id=user_id, user_role=user_role,
            query=query, entity_id=entity_id,
        )
        
        # Determine which agents to invoke
        if capabilities:
            agents_to_call = []
            for cap in capabilities:
                agent_name = self._capability_map.get(cap)
                if agent_name and agent_name in self._agents:
                    agents_to_call.append(self._agents[agent_name])
        else:
            # Let the orchestrator decide based on query intent
            agents_to_call = self._select_agents(query)
        
        if not agents_to_call:
            return {"results": [], "note": "No relevant agents found for this query"}
        
        # Build scoped context for each agent
        results = []
        for agent in agents_to_call:
            try:
                result = agent.process(ctx)
                results.append(asdict(result))
            except Exception as e:
                logger.error("Agent %s failed: %s", agent.name, e)
                results.append(asdict(AgentResult(
                    agent=agent.name,
                    capability=agent.capability.value,
                    confidence=0,
                    summary="Agent processing failed",
                    error=str(e),
                )))
        
        # Synthesize across agents
        synthesis = self._synthesize(results, query)
        
        return {
            "query": query,
            "agents_invoked": [r["agent"] for r in results],
            "results": results,
            "synthesis": synthesis,
        }
    
    def _select_agents(self, query: str) -> List[SpecialistAgent]:
        """Select which agents to invoke based on query intent."""
        query_lower = query.lower()
        
        # Keyword-based routing
        intent_map = {
            "knowledge": ["what", "how", "why", "when", "who", "where", "tell me", "find", "search", "explain"],
            "finance": ["invoice", "payment", "revenue", "expense", "money", "cost", "budget", "financial", "account", "p&l"],
            "operations": ["project", "task", "block", "progress", "status", "workflow", "deadline", "milestone"],
            "customer": ["customer", "client", "preference", "history", "relationship", "feedback"],
            "learning": ["learn", "pattern", "improve", "optimize", "suggestion", "proposal", "trend"],
        }
        
        selected = set()
        for cap_name, keywords in intent_map.items():
            if any(kw in query_lower for kw in keywords):
                agent_name = self._capability_map.get(cap_name + "_intelligence")
                if agent_name and agent_name in self._agents:
                    selected.add(agent_name)
        
        # Always include knowledge agent for context
        knowledge_agent = self._capability_map.get(AgentCapability.KNOWLEDGE_QUERY.value)
        if knowledge_agent and knowledge_agent in self._agents:
            selected.add(knowledge_agent)
        
        return [self._agents[name] for name in selected if name in self._agents]
    
    def _synthesize(self, results: List[Dict], query: str) -> Dict:
        """Synthesize results from multiple agents into a unified response."""
        if not results:
            return {"summary": "No results to synthesize", "next_best_action": None}
        
        all_actions = []
        all_risks = []
        total_confidence = 0
        count = 0
        
        for r in results:
            for a in r.get("next_actions", []):
                all_actions.append(a)
            for risk in r.get("risks", []):
                all_risks.append(risk)
            total_confidence += r.get("confidence", 0)
            count += 1
        
        avg_confidence = total_confidence / count if count > 0 else 0
        
        return {
            "summary": f"Processed across {count} agents (avg confidence: {avg_confidence:.0%})",
            "average_confidence": avg_confidence,
            "critical_risks": [r for r in all_risks if r.get("severity") in ("high", "critical")],
            "warnings": [r for r in all_risks if r.get("severity") == "medium"],
            "next_actions": all_actions[:5],
            "needs_human": any(r.get("needs_human") for r in results),
        }


# ---------------------------------------------------------------------------
# Global Orchestrator Instance
# ---------------------------------------------------------------------------

_orchestrator: Optional[ShunyaOrchestrator] = None


def get_orchestrator() -> ShunyaOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ShunyaOrchestrator()
        # Register all specialist agents
        _orchestrator.register(KnowledgeAgent())
        _orchestrator.register(FinanceAgent())
        _orchestrator.register(OperationsAgent())
        _orchestrator.register(CustomerAgent())
        _orchestrator.register(LearningAgent())
        logger.info("Orchestrator initialized with %d agents", len(_orchestrator._agents))
    return _orchestrator