"""
SHUNYA — Human Context Service (Phase 5)
"""
import json
from datetime import datetime, timezone
from typing import Optional
from app import db
from app.human_context.models import (
    HumanContextItem, ContextProposal, ContextConcept, ContextCategory,
    ScopeType, AssertionType, ContextStatus, ProposalStatus, ValueType,
)
from app.privacy import PrivacyService
from app.privacy.models import MemoryEligibility, SensitivityLevel
from app.models import Person
from app.shunya.identity import IdentityResolver


class HumanContextService:
    """Canonical Human Context service."""

    def __init__(self, session=None):
        self._session = session or db.session
        self._privacy = PrivacyService(session)

    # ------------------------------------------------------------------
    # Proposal
    # ------------------------------------------------------------------

    def propose_context(self, person_id: int, context_key: str, value: str,
                        context_category: str = "other",
                        scope_type: str = "person_global",
                        tenant_id: Optional[int] = None,
                        relationship_id: Optional[int] = None,
                        source_object_type: str = "",
                        source_object_id: Optional[int] = None,
                        assertion_type: str = "explicit",
                        created_by: str = "") -> dict:
        """Propose a context item. Requires approval before commit."""
        proposal = ContextProposal(
            tenant_id=tenant_id, person_id=person_id,
            relationship_id=relationship_id,
            context_category=context_category,
            context_key=context_key, value=value,
            scope_type=scope_type,
            source_object_type=source_object_type,
            source_object_id=source_object_id,
            assertion_type=assertion_type,
            created_by=created_by,
        )
        self._session.add(proposal)
        self._session.commit()
        return {"success": True, "proposal_id": proposal.id, "status": ProposalStatus.PROPOSED}

    def approve_proposal(self, proposal_id: int,
                         tenant_id: Optional[int] = None,
                         approved_by: str = "") -> dict:
        """Approve a proposal and commit as active context if policy permits."""
        proposal = self._session.get(ContextProposal, proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        if tenant_id is not None and proposal.tenant_id != tenant_id:
            return {"success": False, "error": "Proposal not found"}

        # Phase 4 gate
        privacy_result = self._privacy.evaluate_memory_eligibility(
            source_type="context_proposal", source_id=proposal.id,
            tenant_id=tenant_id, person_id=proposal.person_id,
        )
        if privacy_result.get("memory_eligibility") == MemoryEligibility.INELIGIBLE:
            return {"success": False, "error": "Blocked by privacy policy",
                    "privacy_decision": privacy_result}

        # Commit as active context
        item = self.create_explicit_context(
            person_id=proposal.person_id,
            context_key=proposal.context_key,
            value=proposal.value,
            context_category=proposal.context_category,
            scope_type=proposal.scope_type,
            tenant_id=tenant_id,
            relationship_id=proposal.relationship_id,
            source_object_type=proposal.source_object_type,
            source_object_id=proposal.source_object_id,
            assertion_type=proposal.assertion_type,
            created_by=approved_by,
        )

        proposal.status = ProposalStatus.COMMITTED
        proposal.approved_by = approved_by
        proposal.approved_at = datetime.now(timezone.utc)
        self._session.commit()

        return {"success": True, "item_id": item.id, "status": ContextStatus.ACTIVE}

    def reject_proposal(self, proposal_id: int,
                        tenant_id: Optional[int] = None) -> dict:
        proposal = self._session.get(ContextProposal, proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        if tenant_id is not None and proposal.tenant_id != tenant_id:
            return {"success": False, "error": "Proposal not found"}
        proposal.status = ProposalStatus.REJECTED
        self._session.commit()
        return {"success": True, "status": ProposalStatus.REJECTED}

    # ------------------------------------------------------------------
    # Direct creation
    # ------------------------------------------------------------------

    def create_explicit_context(self, person_id: int, context_key: str, value: str,
                                context_category: str = "other",
                                scope_type: str = "person_global",
                                scope_object_type: str = "",
                                scope_object_id: Optional[int] = None,
                                tenant_id: Optional[int] = None,
                                relationship_id: Optional[int] = None,
                                source_object_type: str = "",
                                source_object_id: Optional[int] = None,
                                assertion_type: str = "explicit",
                                valid_until: Optional[datetime] = None,
                                created_by: str = "") -> HumanContextItem:
        """Create a context item directly (explicit deterministic path)."""
        # Supersede existing active context for same key/scope
        existing = self._session.query(HumanContextItem).filter_by(
            person_id=person_id, context_key=context_key,
            scope_type=scope_type, status=ContextStatus.ACTIVE,
        ).first()
        if existing:
            existing.status = ContextStatus.SUPERSEDED
            existing.superseded_by_id = None  # Will set below

        item = HumanContextItem(
            tenant_id=tenant_id, person_id=person_id,
            relationship_id=relationship_id,
            context_category=context_category,
            context_key=context_key, value=value,
            scope_type=scope_type,
            scope_object_type=scope_object_type,
            scope_object_id=scope_object_id,
            source_object_type=source_object_type,
            source_object_id=source_object_id,
            assertion_type=assertion_type,
            status=ContextStatus.ACTIVE,
            valid_from=datetime.now(timezone.utc),
            valid_until=valid_until,
            observed_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self._session.add(item)
        self._session.flush()

        if existing:
            existing.superseded_by_id = item.id
            item.supersedes_id = existing.id

        self._session.commit()
        return item

    def create_manual_context(self, person_id: int, context_key: str, value: str,
                               created_by: str = "", **kwargs) -> HumanContextItem:
        return self.create_explicit_context(
            person_id, context_key, value,
            assertion_type=AssertionType.MANUAL,
            created_by=created_by, **kwargs
        )

    def create_imported_context(self, person_id: int, context_key: str, value: str,
                                 **kwargs) -> HumanContextItem:
        return self.create_explicit_context(
            person_id, context_key, value,
            assertion_type=AssertionType.IMPORTED, **kwargs
        )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_effective_context(self, person_id: int,
                               context_key: Optional[str] = None,
                               scope_type: Optional[str] = None,
                               scope_object_id: Optional[int] = None,
                               at_time: Optional[datetime] = None,
                               tenant_id: Optional[int] = None) -> list[dict]:
        """Get effective context for a Person, resolving scope precedence."""
        now = at_time or datetime.now(timezone.utc)

        q = self._session.query(HumanContextItem).filter_by(
            person_id=person_id, status=ContextStatus.ACTIVE,
        )
        if tenant_id:
            q = q.filter(HumanContextItem.tenant_id == tenant_id)
        if context_key:
            q = q.filter(HumanContextItem.context_key == context_key)
        if scope_type:
            q = q.filter(HumanContextItem.scope_type == scope_type)
        if scope_object_id is not None:
            q = q.filter(HumanContextItem.scope_object_id == scope_object_id)

        items = q.order_by(HumanContextItem.created_at.desc()).all()

        # Filter by time window
        effective = []
        for item in items:
            if item.valid_from and item.valid_from > now:
                continue
            if item.valid_until and item.valid_until < now:
                item.status = ContextStatus.EXPIRED
                continue
            effective.append(item)

        # Sort by precedence: source > lead/opp > relationship > time_window > global
        precedence = {
            ScopeType.SOURCE_OBJECT: 0,
            ScopeType.LEAD_OR_OPPORTUNITY: 1,
            ScopeType.RELATIONSHIP: 2,
            ScopeType.TIME_WINDOW: 3,
            ScopeType.PERSON_GLOBAL: 4,
        }

        # Check for conflicts at same precedence
        by_key = {}
        for item in effective:
            key = item.context_key
            if key not in by_key:
                by_key[key] = {}
            scope = item.scope_type
            if scope not in by_key[key]:
                by_key[key][scope] = []
            by_key[key][scope].append(item)

        results = []
        for key, scopes in by_key.items():
            sorted_scopes = sorted(scopes.keys(), key=lambda s: precedence.get(s, 99))
            for scope in sorted_scopes:
                items_at_scope = scopes[scope]
                if len(items_at_scope) > 1:
                    # Check for conflict
                    values = set(i.value for i in items_at_scope)
                    if len(values) > 1:
                        results.append({
                            "context_key": key, "scope_type": scope,
                            "status": "conflict", "values": list(values),
                            "items": [self._item_to_dict(i) for i in items_at_scope],
                        })
                        continue
                results.append(self._item_to_dict(items_at_scope[0]))
                break  # Highest precedence wins

        return results

    def list_context_for_person(self, person_id: int,
                                 tenant_id: Optional[int] = None) -> list[dict]:
        q = self._session.query(HumanContextItem).filter_by(person_id=person_id)
        if tenant_id:
            q = q.filter(HumanContextItem.tenant_id == tenant_id)
        return [self._item_to_dict(i) for i in q.order_by(HumanContextItem.created_at.desc()).all()]

    def list_context_for_relationship(self, relationship_id: int,
                                       tenant_id: Optional[int] = None) -> list[dict]:
        q = self._session.query(HumanContextItem).filter_by(relationship_id=relationship_id)
        if tenant_id:
            q = q.filter(HumanContextItem.tenant_id == tenant_id)
        return [self._item_to_dict(i) for i in q.order_by(HumanContextItem.created_at.desc()).all()]

    def list_context_for_scope(self, scope_type: str, scope_object_id: int,
                                tenant_id: Optional[int] = None) -> list[dict]:
        q = self._session.query(HumanContextItem).filter_by(
            scope_type=scope_type, scope_object_id=scope_object_id)
        if tenant_id:
            q = q.filter(HumanContextItem.tenant_id == tenant_id)
        return [self._item_to_dict(i) for i in q.order_by(HumanContextItem.created_at.desc()).all()]

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def supersede_context(self, item_id: int, new_value: str,
                           tenant_id: Optional[int] = None,
                           created_by: str = "") -> dict:
        item = self._session.get(HumanContextItem, item_id)
        if not item:
            return {"success": False, "error": "Context not found"}
        if tenant_id is not None and item.tenant_id != tenant_id:
            return {"success": False, "error": "Context not found"}
        new_item = self.create_explicit_context(
            person_id=item.person_id, context_key=item.context_key,
            value=new_value, context_category=item.context_category,
            scope_type=item.scope_type, tenant_id=tenant_id,
            source_object_type=item.source_object_type,
            source_object_id=item.source_object_id,
            assertion_type=item.assertion_type, created_by=created_by,
        )
        return {"success": True, "item_id": new_item.id, "status": ContextStatus.ACTIVE}

    def revoke_context(self, item_id: int, tenant_id: Optional[int] = None) -> dict:
        item = self._session.get(HumanContextItem, item_id)
        if not item:
            return {"success": False, "error": "Context not found"}
        if tenant_id is not None and item.tenant_id != tenant_id:
            return {"success": False, "error": "Context not found"}
        item.status = ContextStatus.REVOKED
        self._session.commit()
        return {"success": True, "status": ContextStatus.REVOKED}

    def invalidate_context(self, item_id: int, tenant_id: Optional[int] = None) -> dict:
        item = self._session.get(HumanContextItem, item_id)
        if not item:
            return {"success": False, "error": "Context not found"}
        if tenant_id is not None and item.tenant_id != tenant_id:
            return {"success": False, "error": "Context not found"}
        item.status = ContextStatus.INVALIDATED
        self._session.commit()
        return {"success": True, "status": ContextStatus.INVALIDATED}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _item_to_dict(self, item: HumanContextItem) -> dict:
        return {
            "id": item.id, "person_id": item.person_id,
            "context_key": item.context_key, "value": item.value,
            "context_category": item.context_category,
            "scope_type": item.scope_type,
            "assertion_type": item.assertion_type,
            "status": item.status,
            "valid_from": item.valid_from.isoformat() if item.valid_from else None,
            "valid_until": item.valid_until.isoformat() if item.valid_until else None,
            "source_object_type": item.source_object_type,
            "source_object_id": item.source_object_id,
            "supersedes_id": item.supersedes_id,
            "superseded_by_id": item.superseded_by_id,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }