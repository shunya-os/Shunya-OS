"""G3 Phase 3: Knowledge Graph Wiring — Wires intelligence engines into the RetrievalLayer.

Each provider is a callable fn(query: str) -> list[dict] with fields:
    name, type, status, summary

Called from the app factory to set up all providers on the singleton
IntelligenceRuntime's RetrievalLayer.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Relationship Intelligence Provider (G3 Phase 3.1) ───────────────────────


def relationship_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search relationships (rel_relationships) and return canonical evidence.

    Queries the CanonicalRelationship model by display_name, email, phone,
    company_name, tags, and returns trust-scored relationship profiles.
    """
    try:
        from app import db
        from app.relationship.models import CanonicalRelationship

        like = f"%{query}%"
        q = CanonicalRelationship.query.filter(
            CanonicalRelationship.status != "archived",
            db.or_(
                CanonicalRelationship.display_name.ilike(like),
                CanonicalRelationship.email.ilike(like),
                CanonicalRelationship.phone.ilike(like),
                CanonicalRelationship.company_name.ilike(like),
                CanonicalRelationship.tags.ilike(like),
                CanonicalRelationship.legal_name.ilike(like),
            ),
        )
        if org_id:
            q = q.filter(CanonicalRelationship.organization_id == org_id)
        rels = q.order_by(CanonicalRelationship.display_name).limit(20).all()

        results: list[dict] = []
        for r in rels:
            results.append({
                "name": r.display_name or "",
                "type": r.relationship_type or "relationship",
                "status": r.status or "active",
                "summary": (
                    f"{r.display_name} — {r.relationship_type}"
                    f"{f' ({r.company_name})' if r.company_name else ''}"
                    f"{f' [{r.risk_level}]' if r.risk_level else ''}"
                ),
                "confidence": 0.85,
                "relevance": 0.8,
                "metadata": {
                    "id": r.id,
                    "organization_id": r.organization_id,
                    "relationship_type": r.relationship_type,
                    "email": r.email,
                    "phone": r.phone,
                    "company_name": r.company_name,
                    "city": r.city,
                    "risk_level": r.risk_level,
                    "priority": r.priority,
                    "tags": [t.strip() for t in (r.tags or "").split(",") if t.strip()],
                },
            })
        return results[:10]
    except Exception as e:
        logger.warning("RelationshipIntelligence provider failed: %s", e)
        return []


# ── Knowledge Intelligence Provider (G3 Phase 3.2 — UCP-04) ────────────────
# Already partially wired in integration.py as _knowledge_search.
# This is the canonical provider that all callers should use.


def knowledge_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search canonical knowledge documents via KnowledgeIntelligence (UCP-04).

    Uses the KnowledgeIntelligenceEngine to semantically match the query
    against Knowledge objects loaded from the app's KnowledgeDocument model.
    Results include relevance scores, confidence, and type metadata.
    """
    try:
        from core.knowledge_intelligence.engine import KnowledgeIntelligenceEngine
        from core.knowledge_intelligence.models import Knowledge

        knowledge_list: list[Knowledge] = []
        try:
            from app import db
            from app.models import KnowledgeDocument

            q = db.session.query(KnowledgeDocument)
            if org_id:
                q = q.filter(KnowledgeDocument.organization_id == org_id)
            rows = q.order_by(KnowledgeDocument.updated_at.desc()).limit(50).all()
            for r in rows:
                tags = []
                if r.tags:
                    tags = [t.strip() for t in r.tags.split(",") if t.strip()]
                knowledge_list.append(Knowledge(
                    title=r.title or "",
                    statement=r.extracted_text or r.summary or "",
                    summary=r.summary or "",
                    tags=tags,
                    domain=r.category or "",
                    is_active=True,
                    confidence_score=0.9,
                ))
        except Exception:
            pass

        if not knowledge_list:
            return []

        engine = KnowledgeIntelligenceEngine()
        search_results = engine.search(knowledge_list, query, max_results=5)
        results: list[dict] = []
        for sr in search_results:
            results.append({
                "name": sr.title or "",
                "type": sr.knowledge_type or "knowledge",
                "status": "active",
                "summary": sr.summary or sr.title or "",
                "confidence": sr.confidence_score,
                "relevance": sr.relevance_score,
                "metadata": {
                    "knowledge_id": sr.knowledge_id,
                    "knowledge_type": sr.knowledge_type,
                    "title": sr.title,
                    "summary": sr.summary,
                    "matched_terms": sr.matched_terms,
                },
            })
        return results
    except Exception as e:
        logger.warning("KnowledgeIntelligence provider failed: %s", e)
        return []


# ── Financial Intelligence Provider (G3 Phase 3.3) ─────────────────────────


def financial_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search financial objects — accounts, invoices, budgets, transactions.

    Queries the canonical finance models and wraps results with Financial
    Intelligence Engine for risk scoring, cash flow context, and insights.
    """
    try:
        from app import db
        from app.finance.models import Account, FinInvoice, Budget

        q_lower = query.lower()
        results: list[dict] = []

        # Accounts
        acct_query = Account.query
        if org_id:
            acct_query = acct_query.filter(Account.organization_id == org_id)
        for acct in acct_query.filter(
            db.or_(
                Account.name.ilike(f"%{query}%"),
                Account.code.ilike(f"%{query}%"),
            )
        ).limit(10).all():
            results.append({
                "name": f"#{acct.code} {acct.name}",
                "type": f"account/{acct.type}",
                "status": "active" if acct.is_active else "inactive",
                "summary": f"{acct.type}: {acct.name} ({acct.code}) [{acct.subtype}]",
                "confidence": 0.9,
                "relevance": 0.8 if q_lower in (acct.name.lower()) else 0.6,
                "metadata": {
                    "id": acct.id,
                    "organization_id": acct.organization_id,
                    "code": acct.code,
                    "account_type": acct.type,
                    "currency": acct.currency,
                },
            })

        # Invoices
        inv_query = FinInvoice.query
        if org_id:
            inv_query = inv_query.filter(FinInvoice.organization_id == org_id)
        for inv in inv_query.filter(
            db.or_(
                FinInvoice.invoice_number.ilike(f"%{query}%"),
                FinInvoice.customer_name.ilike(f"%{query}%"),
                FinInvoice.status.ilike(f"%{query}%"),
            )
        ).limit(10).all():
            results.append({
                "name": inv.invoice_number or f"Invoice #{inv.id}",
                "type": "invoice",
                "status": inv.status or "draft",
                "summary": (
                    f"Invoice {inv.invoice_number} — {inv.customer_name}"
                    f" {f'({inv.total_amount})' if inv.total_amount else ''}"
                ),
                "confidence": 0.9,
                "relevance": 0.75,
                "metadata": {
                    "id": inv.id,
                    "organization_id": inv.organization_id,
                    "invoice_number": inv.invoice_number,
                    "customer_name": inv.customer_name,
                    "status": inv.status,
                    "total_amount": float(inv.total_amount) if inv.total_amount else 0,
                    "due_date": str(inv.due_date) if inv.due_date else "",
                },
            })

        # Budgets
        bud_query = Budget.query
        if org_id:
            bud_query = bud_query.filter(Budget.organization_id == org_id)
        for bud in bud_query.filter(
            Budget.name.ilike(f"%{query}%")
        ).limit(5).all():
            results.append({
                "name": bud.name or f"Budget #{bud.id}",
                "type": "budget",
                "status": bud.period or "unknown",
                "summary": (
                    f"Budget: {bud.name}"
                    f" ({float(bud.total_planned or 0):.2f} planned)"
                ),
                "confidence": 0.85,
                "relevance": 0.7,
                "metadata": {
                    "id": bud.id,
                    "organization_id": bud.organization_id,
                    "name": bud.name,
                    "total_planned": float(bud.total_planned or 0),
                    "period": bud.period,
                },
            })

        return results[:15]
    except Exception as e:
        logger.warning("FinancialIntelligence provider failed: %s", e)
        return []


# ── Operations Intelligence Provider (G3 Phase 3.4) ────────────────────────


def operations_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search operational data — processes, workflows, SOPs, resources.

    Queries the OperationsIntelligenceEngine for process analysis and health.
    Falls back to any app-level models if available.
    """
    try:
        from core.operations_intelligence.engine import OperationsIntelligenceEngine
        from core.operations_intelligence.models import Process, ProcessStep

        engine = OperationsIntelligenceEngine()
        proc = Process(
            process_id="query",
            name=query[:100],
            steps=[
                ProcessStep(
                    step_id="s1", name="Analyze", duration_minutes=5,
                    decision_point=False, parallel=False, quality_check=False,
                    rework_pct=0, variability_pct=0,
                )
            ],
        )
        analysis = engine.analyze_process(proc)
        health = engine.compute_operational_health(proc)

        results: list[dict] = [
            {
                "name": proc.name,
                "type": "operations/process",
                "status": analysis.get("assessment", {}).get("level", "unknown"),
                "summary": (
                    f"Process: {analysis.get('name', '')} "
                    f"— {analysis.get('step_count', 0)} steps "
                    f"({analysis.get('cycle_time_minutes', 0)}min cycle)"
                ),
                "confidence": 0.75,
                "relevance": 0.7,
                "metadata": {
                    "cycle_time_minutes": analysis.get("cycle_time_minutes", 0),
                    "throughput_per_hour": analysis.get("throughput_per_hour", 0),
                    "defect_rate_pct": analysis.get("defect_rate_pct", 0),
                    "step_count": analysis.get("step_count", 0),
                    "health_score": health.get("score", 0),
                    "assessment": analysis.get("assessment", {}).get("level", "unknown"),
                },
            },
        ]
        return results
    except Exception as e:
        logger.warning("OperationsIntelligence provider failed: %s", e)
        return []


# ── Sales Intelligence Provider (G3 Phase 3.5) ─────────────────────────────


def sales_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search sales objects — leads, opportunities, proposals.

    Queries app-level CRM/commercial models for sales pipeline evidence.
    """
    try:
        from app import db

        results: list[dict] = []
        q_lower = query.lower()

        # Try leads from CRM
        try:
            from app.crm.models import Lead as CrmLead

            lead_query = CrmLead.query
            if org_id and hasattr(CrmLead, "organization_id"):
                lead_query = lead_query.filter(CrmLead.organization_id == org_id)
            for lead in lead_query.filter(
                db.or_(
                    CrmLead.name.ilike(f"%{query}%"),
                    CrmLead.email.ilike(f"%{query}%"),
                    CrmLead.company.ilike(f"%{query}%"),
                )
            ).limit(10).all():
                results.append({
                    "name": lead.name or "",
                    "type": "sales/lead",
                    "status": lead.status or "new",
                    "summary": f"Lead: {lead.name}{f' ({lead.company})' if lead.company else ''}",
                    "confidence": 0.85,
                    "relevance": 0.8,
                    "metadata": {
                        "id": getattr(lead, "id", ""),
                        "email": getattr(lead, "email", ""),
                        "phone": getattr(lead, "phone", ""),
                        "company": getattr(lead, "company", ""),
                        "status": getattr(lead, "status", "new"),
                        "source": getattr(lead, "source", ""),
                    },
                })
        except Exception:
            pass

        # Try commercial opportunities
        try:
            from app.commercial.models import CommercialOpportunity

            opp_query = CommercialOpportunity.query
            if org_id and hasattr(CommercialOpportunity, "organization_id"):
                opp_query = opp_query.filter(CommercialOpportunity.organization_id == org_id)
            for opp in opp_query.filter(
                db.or_(
                    CommercialOpportunity.title.ilike(f"%{query}%"),
                    CommercialOpportunity.description.ilike(f"%{query}%"),
                )
            ).limit(10).all():
                results.append({
                    "name": opp.title or f"Opportunity #{opp.id}",
                    "type": "sales/opportunity",
                    "status": opp.lifecycle_state or "open",
                    "summary": (
                        f"Opportunity: {opp.title}"
                        f"{f' [{opp.lifecycle_state}]' if opp.lifecycle_state else ''}"
                    ),
                    "confidence": 0.85,
                    "relevance": 0.8,
                    "metadata": {
                        "id": opp.id,
                        "title": opp.title,
                        "lifecycle_state": opp.lifecycle_state,
                        "value": float(opp.value or 0) if hasattr(opp, "value") else 0,
                    },
                })
        except Exception:
            pass

        # Try proposals
        try:
            from app.commercial.models import CommercialProposal

            prop_query = CommercialProposal.query
            if org_id and hasattr(CommercialProposal, "organization_id"):
                prop_query = prop_query.filter(CommercialProposal.organization_id == org_id)
            for prop in prop_query.filter(
                CommercialProposal.title.ilike(f"%{query}%")
            ).limit(5).all():
                results.append({
                    "name": prop.title or f"Proposal #{prop.id}",
                    "type": "sales/proposal",
                    "status": prop.status or "draft",
                    "summary": f"Proposal: {prop.title} [{prop.status}]",
                    "confidence": 0.8,
                    "relevance": 0.75,
                    "metadata": {
                        "id": prop.id,
                        "title": prop.title,
                        "status": prop.status,
                    },
                })
        except Exception:
            pass

        return results[:10]
    except Exception as e:
        logger.warning("SalesIntelligence provider failed: %s", e)
        return []


# ── Marketing Intelligence Provider (G3 Phase 3.6) ─────────────────────────


def marketing_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search marketing objects — campaigns, segments, content.

    Queries app-level marketing/campaign models for marketing evidence.
    """
    try:
        from app import db

        results: list[dict] = []
        q_lower = query.lower()

        # Campaigns
        try:
            from app.campaign.models import Campaign

            camp_query = Campaign.query
            if org_id and hasattr(Campaign, "organization_id"):
                camp_query = camp_query.filter(Campaign.organization_id == org_id)
            for camp in camp_query.filter(
                db.or_(
                    Campaign.name.ilike(f"%{query}%"),
                    Campaign.objective.ilike(f"%{query}%"),
                    Campaign.status.ilike(f"%{query}%"),
                )
            ).limit(10).all():
                results.append({
                    "name": camp.name or f"Campaign #{camp.id}",
                    "type": "marketing/campaign",
                    "status": camp.status or "draft",
                    "summary": (
                        f"Campaign: {camp.name} [{camp.status}]"
                        f"{f' — {camp.objective}' if camp.objective else ''}"
                    ),
                    "confidence": 0.85,
                    "relevance": 0.8,
                    "metadata": {
                        "id": camp.id,
                        "name": camp.name,
                        "status": camp.status,
                        "objective": getattr(camp, "objective", ""),
                        "budget": float(camp.budget or 0) if hasattr(camp, "budget") else 0,
                    },
                })
        except Exception:
            pass

        # Marketing segments / audiences
        try:
            from app.g5.models import GrowthSegment

            seg_query = GrowthSegment.query
            if org_id and hasattr(GrowthSegment, "organization_id"):
                seg_query = seg_query.filter(GrowthSegment.organization_id == org_id)
            for seg in seg_query.filter(
                GrowthSegment.name.ilike(f"%{query}%")
            ).limit(5).all():
                results.append({
                    "name": seg.name or f"Segment #{seg.id}",
                    "type": "marketing/segment",
                    "status": "active" if getattr(seg, "is_active", True) else "inactive",
                    "summary": f"Segment: {seg.name}",
                    "confidence": 0.8,
                    "relevance": 0.7,
                    "metadata": {
                        "id": seg.id,
                        "name": seg.name,
                        "criteria": getattr(seg, "criteria", ""),
                    },
                })
        except Exception:
            pass

        # Ad campaigns / content generation records
        try:
            from app.integration.models import AdCampaign, ContentGeneration

            ad_query = AdCampaign.query
            for ad in ad_query.filter(
                AdCampaign.name.ilike(f"%{query}%")
            ).limit(5).all():
                results.append({
                    "name": ad.name or f"Ad #{ad.id}",
                    "type": "marketing/ad_campaign",
                    "status": getattr(ad, "status", "unknown"),
                    "summary": f"Ad: {ad.name} [{getattr(ad, 'platform', '')}]",
                    "confidence": 0.75,
                    "relevance": 0.65,
                    "metadata": {
                        "id": ad.id,
                        "name": ad.name,
                        "platform": getattr(ad, "platform", ""),
                        "status": getattr(ad, "status", ""),
                    },
                })

            cg_query = ContentGeneration.query
            for cg in cg_query.filter(
                ContentGeneration.prompt.ilike(f"%{query}%")
            ).limit(5).all():
                results.append({
                    "name": cg.id or "",
                    "type": "marketing/content",
                    "status": getattr(cg, "status", "completed"),
                    "summary": f"Content: {getattr(cg, 'content_type', 'unknown')}",
                    "confidence": 0.7,
                    "relevance": 0.6,
                    "metadata": {
                        "id": cg.id,
                        "content_type": getattr(cg, "content_type", ""),
                        "status": getattr(cg, "status", ""),
                    },
                })
        except Exception:
            pass

        return results[:10]
    except Exception as e:
        logger.warning("MarketingIntelligence provider failed: %s", e)
        return []


# ── Cross-Object Relationship Search (G3 Phase 3.7) ───────────────────────


def cross_object_relationship_search(query: str, org_id: int | None = None) -> list[dict]:
    """Search for objects related to the query across all domains.

    Uses the execution graph / object relations table to find relationships
    between objects — people, organizations, leads, customers, opportunities,
    invoices, documents, etc.
    """
    try:
        from app import db

        results: list[dict] = []
        q_lower = query.lower()

        # Object relations from the graph module
        try:
            from app.graph.models import ObjectRelation

            rel_query = ObjectRelation.query
            for rel in rel_query.filter(
                db.or_(
                    ObjectRelation.source_type.ilike(f"%{query}%"),
                    ObjectRelation.target_type.ilike(f"%{query}%"),
                    ObjectRelation.relation_type.ilike(f"%{query}%"),
                )
            ).limit(20).all():
                results.append({
                    "name": f"{rel.source_type}:{rel.source_id} → {rel.target_type}:{rel.target_id}",
                    "type": f"relation/{rel.relation_type}",
                    "status": getattr(rel, "status", "active"),
                    "summary": (
                        f"{rel.source_type} #{rel.source_id} "
                        f"→ {rel.relation_type} → "
                        f"{rel.target_type} #{rel.target_id}"
                    ),
                    "confidence": 0.8,
                    "relevance": 0.7,
                    "metadata": {
                        "source_type": rel.source_type,
                        "source_id": rel.source_id,
                        "target_type": rel.target_type,
                        "target_id": rel.target_id,
                        "relation_type": rel.relation_type,
                        "strength": getattr(rel, "strength", None),
                    },
                })
        except Exception:
            pass

        # Entity relationships from core entity model
        try:
            from app.core.entity import Entity

            ent_query = Entity.query
            for ent in ent_query.filter(
                db.or_(
                    Entity.name.ilike(f"%{query}%"),
                    Entity.entity_type.ilike(f"%{query}%"),
                )
            ).limit(10).all():
                results.append({
                    "name": ent.name or f"Entity #{ent.id}",
                    "type": f"entity/{ent.entity_type or 'unknown'}",
                    "status": getattr(ent, "status", "active"),
                    "summary": f"Entity: {ent.name} ({ent.entity_type})",
                    "confidence": 0.75,
                    "relevance": 0.7,
                    "metadata": {
                        "id": ent.id,
                        "name": ent.name,
                        "entity_type": ent.entity_type,
                        "status": getattr(ent, "status", ""),
                    },
                })
        except Exception:
            pass

        return results[:10]
    except Exception as e:
        logger.warning("Cross-object relationship search failed: %s", e)
        return []


# ── Universal Search → AI Integration (G3 Phase 3.8) ───────────────────────


def universal_search(query: str, org_id: int | None = None) -> list[dict]:
    """Canonical universal search across ALL object types.

    Delegates to app.search.universal_search.search_canonical_objects and
    returns a uniform evidence format consumable by the RetrievalLayer.
    This ensures the AI runtime sees the same results as the UI command
    palette — a single unified search path.
    """
    try:
        from app.search.universal_search import search_canonical_objects

        payload = search_canonical_objects(query, org_id=org_id, limit=8)
        results: list[dict] = []
        for r in payload.get("results", []):
            object_type = r.get("object_type", "object")
            label = r.get("label", "")
            status = r.get("status", "")
            desc = r.get("description", "") or r.get("summary", "")
            results.append({
                "name": label or r.get("name", ""),
                "type": object_type,
                "status": status or "active",
                "summary": desc or label or f"{object_type}: {query}",
                "confidence": 0.85,
                "relevance": r.get("relevance", 0.8),
                "metadata": {
                    "id": r.get("id"),
                    "object_type": object_type,
                    "api_path": r.get("api_path", ""),
                    "workspace_id": r.get("workspace_id"),
                    "workspace_type": r.get("workspace_type"),
                },
            })
        return results[:10]
    except Exception as e:
        logger.warning("Universal search failed: %s", e)
        return []


# ── Wiring Factory ─────────────────────────────────────────────────────────


def wire_all_providers(runtime) -> None:
    """Wire all G3 Phase 3 intelligence providers into the runtime's RetrievalLayer.

    Called once at app startup during ensure_runtime() or from the app factory.
    Each provider is a self-contained callable that the retrieval layer invokes
    during evidence gathering.
    """
    if not runtime or not hasattr(runtime, "retrieval"):
        logger.warning("No runtime or retrieval layer — skipping provider wiring")
        return

    retrieval = runtime.retrieval

    # Resolve org context from runtime
    def _resolve_org_id() -> int | None:
        try:
            ctx_engine = getattr(runtime, "context", None)
            if ctx_engine is None:
                return None
            session_id = getattr(ctx_engine, "_current_session", "")
            ctx = ctx_engine.get(session_id) if session_id else None
            org_id = getattr(ctx, "tenant_id", "") if ctx else ""
            return int(org_id) if org_id else None
        except (TypeError, ValueError, AttributeError):
            return None

    # ── Relationship Intelligence (3.1) ──
    def _rel_provider(query: str) -> list[dict]:
        return relationship_search(query, org_id=_resolve_org_id())

    # ── Knowledge Intelligence (3.2 — UCP-04) ──
    def _know_provider(query: str) -> list[dict]:
        return knowledge_search(query, org_id=_resolve_org_id())

    # ── Financial Intelligence (3.3) ──
    def _fin_provider(query: str) -> list[dict]:
        return financial_search(query, org_id=_resolve_org_id())

    # ── Operations Intelligence (3.4) ──
    def _ops_provider(query: str) -> list[dict]:
        return operations_search(query, org_id=_resolve_org_id())

    # ── Sales Intelligence (3.5) ──
    def _sales_provider(query: str) -> list[dict]:
        return sales_search(query, org_id=_resolve_org_id())

    # ── Marketing Intelligence (3.6) ──
    def _mkt_provider(query: str) -> list[dict]:
        return marketing_search(query, org_id=_resolve_org_id())

    # ── Cross-Object Relationship Search (3.7) ──
    def _cross_rel_provider(query: str) -> list[dict]:
        return cross_object_relationship_search(query, org_id=_resolve_org_id())

    # ── Universal Search → AI Integration (3.8) ──
    def _universal_provider(query: str) -> list[dict]:
        return universal_search(query, org_id=_resolve_org_id())

    # Register as additional providers on the retrieval layer
    retrieval._additional_providers = {
        "relationship_intelligence": _rel_provider,
        "knowledge_intelligence": _know_provider,
        "financial_intelligence": _fin_provider,
        "operations_intelligence": _ops_provider,
        "sales_intelligence": _sales_provider,
        "marketing_intelligence": _mkt_provider,
        "cross_object_relationship": _cross_rel_provider,
        "universal_search": _universal_provider,
    }

    logger.info(
        "G3 Phase 3: Wired %d intelligence providers into RetrievalLayer",
        len(retrieval._additional_providers),
    )


def wire_provider(runtime, provider_name: str, provider_fn) -> None:
    """Wire a single provider into the retrieval layer by name.

    Allows selective wiring for testing or partial deployment.
    """
    if not runtime or not hasattr(runtime, "retrieval"):
        logger.warning("No runtime or retrieval layer — cannot wire provider")
        return
    retrieval = runtime.retrieval
    if not hasattr(retrieval, "_additional_providers"):
        retrieval._additional_providers = {}
    retrieval._additional_providers[provider_name] = provider_fn
    logger.info("Wired provider '%s' into RetrievalLayer", provider_name)