"""Shunya Learning Engine — structured proposals with governance gate.

The learning loop:
OBSERVATION → PATTERN → LEARNING PROPOSAL → GOVERNANCE → KNOWLEDGE UPDATE

Learning consumes: decisions, plans, executions, observations, outcomes, corrections.
Learning identifies: repeated patterns, anomalies, successful approaches, failures.
Learning PROPOSES — it does NOT silently rewrite organizational truth.
"""
import json, logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from app import db
from app.models import KnowledgeEntry, Entity, ActivityLog, AIFeedback, EntityDefinition
from app.shunya.foundation import Result

logger = logging.getLogger("app.shunya.learning")


class LearningStatus(str, Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    SUPERSEDED = "superseded"


class LearningEngine:
    """Identifies patterns from observations and produces governed learning proposals."""

    # Minimum evidence threshold for automatic proposal
    MIN_EVIDENCE_COUNT = 3
    MIN_CONFIDENCE_FOR_AUTO_APPROVE = 0.9

    @staticmethod
    def scan_for_patterns(tenant_id: int) -> List[Dict]:
        """Scan recent observations and outcomes for detectable patterns.
        
        Returns a list of potential learning proposals.
        """
        proposals = []
        now = datetime.utcnow()
        
        # 1. STATUS TRANSITION PATTERNS
        proposals.extend(LearningEngine._scan_status_patterns(tenant_id))
        
        # 2. FEEDBACK / CORRECTION PATTERNS
        proposals.extend(LearningEngine._scan_correction_patterns(tenant_id))
        
        # 3. OUTCOME PATTERNS (success vs failure)
        proposals.extend(LearningEngine._scan_outcome_patterns(tenant_id))
        
        # 4. KNOWLEDGE GAP DETECTION
        proposals.extend(LearningEngine._scan_knowledge_gaps(tenant_id))
        
        # 5. STALE KNOWLEDGE
        proposals.extend(LearningEngine._scan_stale_knowledge(tenant_id))
        
        return proposals

    @staticmethod
    def _scan_status_patterns(tenant_id: int) -> List[Dict]:
        """Find patterns in entity status transitions."""
        proposals = []
        
        # Look for entities that get stuck at a particular status
        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        
        for definition in definitions:
            statuses = definition.statuses or []
            for status in statuses[:-1]:  # Skip final status
                # Count entities stuck in this status for 7+ days
                stuck_count = Entity.query.filter(
                    Entity.tenant_id == tenant_id,
                    Entity.definition_id == definition.id,
                    Entity.status == status,
                    Entity.is_archived == False,
                    Entity.updated_at < datetime.utcnow() - timedelta(days=7),
                ).count()
                
                if stuck_count >= 3:
                    next_status = statuses[statuses.index(status) + 1] if statuses.index(status) + 1 < len(statuses) else "completed"
                    proposals.append({
                        "type": "status_bottleneck",
                        "title": f"Entities stuck at '{status}'",
                        "description": f"{stuck_count} {definition.label} entities have been in '{status}' for 7+ days",
                        "recommendation": f"Consider auto-advancing to '{next_status}' after 7 days of inactivity",
                        "evidence_count": stuck_count,
                        "confidence": min(0.5 + (stuck_count * 0.1), 0.9),
                        "entity_type": definition.label,
                        "icon": "🔄",
                    })
        
        return proposals

    @staticmethod
    def _scan_correction_patterns(tenant_id: int) -> List[Dict]:
        """Find patterns in AI feedback corrections."""
        proposals = []
        
        # Find repeated corrections on similar topics
        recent_errors = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.correction.isnot(None),
            AIFeedback.created_at >= datetime.utcnow() - timedelta(days=30),
        ).all()
        
        if len(recent_errors) >= LearningEngine.MIN_EVIDENCE_COUNT:
            # Count corrections by keyword
            keyword_counts = {}
            for fb in recent_errors:
                query = (fb.query or "").lower()
                # Extract key terms
                for word in query.split()[:5]:
                    if len(word) > 3:
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1
            
            # Find the most corrected topic
            if keyword_counts:
                top_keyword = max(keyword_counts, key=keyword_counts.get)
                count = keyword_counts[top_keyword]
                if count >= 2:
                    proposals.append({
                        "type": "repeated_correction",
                        "title": f"Repeated AI corrections about '{top_keyword}'",
                        "description": f"Users corrected AI responses {count} times on this topic in the last 30 days",
                        "recommendation": f"Review and update knowledge base entries related to '{top_keyword}'",
                        "evidence_count": count,
                        "confidence": min(0.5 + (count * 0.15), 0.95),
                        "source": "user_corrections",
                        "icon": "✏️",
                    })
        
        return proposals

    @staticmethod
    def _scan_outcome_patterns(tenant_id: int) -> List[Dict]:
        """Find patterns in successful vs failed outcomes."""
        proposals = []
        
        # Look at recent activity logs for outcome-related patterns
        recent_activities = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.created_at >= datetime.utcnow() - timedelta(days=14),
        ).order_by(ActivityLog.created_at.desc()).limit(100).all()
        
        # Count action types
        action_counts = {}
        for a in recent_activities:
            action = a.action or "unknown"
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Find dominant action patterns
        for action, count in action_counts.items():
            if count >= 5 and action.startswith("executor."):
                proposals.append({
                    "type": "frequent_execution",
                    "title": f"High frequency: {action.replace('executor.', '')}",
                    "description": f"Executed {count} times in the last 14 days",
                    "recommendation": f"Consider creating a shortcut or automation for this action",
                    "evidence_count": count,
                    "confidence": min(0.4 + (count * 0.05), 0.85),
                    "icon": "⚡",
                })
        
        return proposals

    @staticmethod
    def _scan_knowledge_gaps(tenant_id: int) -> List[Dict]:
        """Find patterns in unanswered queries (knowledge gaps)."""
        proposals = []
        
        # Find queries that returned no results (empty responses)
        # Look at AIFeedback entries with corrections that indicate knowledge gaps
        gap_indicators = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.correction.ilike("%don't know%"),
        ).limit(5).all()
        
        if len(gap_indicators) >= 2:
            proposals.append({
                "type": "knowledge_gap",
                "title": "Knowledge gaps detected",
                "description": f"AI couldn't answer {len(gap_indicators)} queries adequately",
                "recommendation": "Upload relevant documents on the Ingest page to fill these gaps",
                "evidence_count": len(gap_indicators),
                "confidence": 0.6,
                "icon": "📚",
            })
        
        return proposals

    @staticmethod
    def _scan_stale_knowledge(tenant_id: int) -> List[Dict]:
        """Find knowledge entries that may be stale."""
        proposals = []
        
        # Find entries not accessed in 90+ days
        stale = KnowledgeEntry.query.filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.use_count <= 1,
            KnowledgeEntry.created_at < datetime.utcnow() - timedelta(days=90),
            KnowledgeEntry.source != "onboarding",  # Don't flag onboarding defaults
        ).limit(10).count()
        
        if stale >= 3:
            proposals.append({
                "type": "stale_knowledge",
                "title": f"{stale} knowledge entries may be stale",
                "description": f"These entries haven't been used in 90+ days. They may be outdated or irrelevant.",
                "recommendation": "Review and archive unused knowledge entries",
                "evidence_count": stale,
                "confidence": 0.5,
                "icon": "🗑️",
            })
        
        return proposals

    @staticmethod
    def propose(tenant_id: int, user_id: int, pattern: Dict) -> Result:
        """Create a formal learning proposal from a detected pattern.
        
        The proposal goes through governance before becoming knowledge.
        """
        from app.shunya.governance import GovernanceEngine, GovernanceLevel
        
        # Check if similar proposal already exists
        existing = KnowledgeEntry.query.filter(
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.question == f"learning.proposal:{pattern.get('title', 'unknown')}",
            KnowledgeEntry.category == "learning",
        ).first()
        
        if existing:
            return Result(success=False, error="Similar proposal already exists")
        
        # Create learning proposal as a knowledge entry
        proposal_content = json.dumps({
            "type": pattern.get("type", "general"),
            "title": pattern.get("title", ""),
            "description": pattern.get("description", ""),
            "recommendation": pattern.get("recommendation", ""),
            "evidence_count": pattern.get("evidence_count", 0),
            "detected_confidence": pattern.get("confidence", 0.5),
            "entity_type": pattern.get("entity_type"),
            "source": pattern.get("source", "auto_detected"),
            "proposed_at": datetime.utcnow().isoformat(),
            "proposed_by": user_id,
            "status": LearningStatus.PROPOSED.value,
        })
        
        # Determine governance level based on confidence and impact
        confidence = pattern.get("confidence", 0.5)
        if confidence >= LearningEngine.MIN_CONFIDENCE_FOR_AUTO_APPROVE:
            governance = GovernanceLevel.AUTO
        elif confidence >= 0.7:
            governance = GovernanceLevel.DRAFT
        else:
            governance = GovernanceLevel.GOVERN
        
        entry = KnowledgeEntry(
            tenant_id=tenant_id,
            question=f"learning.proposal:{pattern.get('title', 'unknown')}",
            answer=proposal_content,
            source=f"learning_engine.{pattern.get('type', 'general')}",
            confidence=confidence,
            category="learning",
            meta_data=json.dumps({
                "status": LearningStatus.PROPOSED.value,
                "governance": governance.value,
                "evidence": pattern.get("evidence_count", 0),
                "type": pattern.get("type", "general"),
            }),
        )
        db.session.add(entry)
        
        # Log the proposal
        activity = ActivityLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="learning.proposed",
            detail=f"Pattern: {pattern.get('title')} (confidence: {confidence}, governance: {governance.value})",
        )
        db.session.add(activity)
        db.session.commit()
        
        return Result(success=True, data={
            "proposal_id": entry.id,
            "title": pattern.get("title"),
            "governance": governance.value,
            "confidence": confidence,
        })

    @staticmethod
    def review_proposal(proposal_id: int, tenant_id: int, user_id: int,
                         decision: str, feedback: Optional[str] = None) -> Result:
        """Review a learning proposal — approve, reject, or request more evidence."""
        entry = KnowledgeEntry.query.filter_by(
            id=proposal_id, tenant_id=tenant_id, category="learning"
        ).first()
        
        if not entry:
            return Result(success=False, error="Proposal not found")
        
        meta = {}
        if entry.meta_data:
            try:
                meta = json.loads(entry.meta_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        if decision == "approve":
            meta["status"] = LearningStatus.APPROVED.value
            meta["approved_at"] = datetime.utcnow().isoformat()
            meta["approved_by"] = user_id
            
            # Apply the learning — update knowledge base
            try:
                proposal = json.loads(entry.answer)
                LearningEngine._apply_learning(tenant_id, proposal)
            except (json.JSONDecodeError, TypeError):
                pass
            
            logger.info("Learning proposal %d approved by user %d", proposal_id, user_id)
            
        elif decision == "reject":
            meta["status"] = LearningStatus.REJECTED.value
            meta["rejected_at"] = datetime.utcnow().isoformat()
            meta["rejected_by"] = user_id
            meta["rejection_reason"] = feedback or "No reason provided"
            
        elif decision == "request_more":
            meta["status"] = LearningStatus.NEEDS_MORE_EVIDENCE.value
            meta["requested_by"] = user_id
            meta["requested_feedback"] = feedback or "Please provide more evidence"
            
        else:
            return Result(success=False, error=f"Unknown decision: {decision}")
        
        entry.meta_data = json.dumps(meta)
        entry.answer = entry.answer  # Preserve content
        
        activity = ActivityLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"learning.{decision}",
            detail=f"Proposal #{proposal_id}: {feedback or decision}",
        )
        db.session.add(activity)
        db.session.commit()
        
        return Result(success=True, data={
            "proposal_id": proposal_id,
            "status": meta["status"],
            "decision": decision,
        })

    @staticmethod
    def _apply_learning(tenant_id: int, proposal: Dict):
        """Apply approved learning to the knowledge base."""
        recommendation = proposal.get("recommendation", "")
        title = proposal.get("title", "Learning")
        
        if not recommendation:
            return
        
        # Store as semantic memory for future reference
        from app.shunya.memory import MemoryStore, MemoryClass
        MemoryStore.store(
            MemoryClass.LEARNING, tenant_id,
            key=f"learning:{title.lower().replace(' ', '_')[:50]}",
            content=recommendation,
            source="learning_engine.approved",
            confidence=proposal.get("detected_confidence", 0.5),
            tags=["learning", "approved", proposal.get("type", "general")],
            metadata={
                "source_proposal": title,
                "evidence_count": proposal.get("evidence_count", 0),
                "applied_at": datetime.utcnow().isoformat(),
            },
        )
        logger.info("Applied learning: %s", title)

    @staticmethod
    def get_proposals(tenant_id: int, status: Optional[str] = None,
                       limit: int = 50) -> List[Dict]:
        """Get learning proposals, optionally filtered by status."""
        filters = [
            KnowledgeEntry.tenant_id == tenant_id,
            KnowledgeEntry.category == "learning",
        ]
        
        entries = KnowledgeEntry.query.filter(*filters)\
            .order_by(KnowledgeEntry.created_at.desc()).limit(limit).all()
        
        results = []
        for e in entries:
            meta = {}
            if e.meta_data:
                try:
                    meta = json.loads(e.meta_data)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            proposal = {}
            try:
                proposal = json.loads(e.answer)
            except (json.JSONDecodeError, TypeError):
                proposal = {"title": e.question, "description": e.answer[:200]}
            
            proposal_status = meta.get("status", LearningStatus.PROPOSED.value)
            
            if status and proposal_status != status:
                continue
            
            results.append({
                "id": e.id,
                "title": proposal.get("title", "Learning Proposal"),
                "description": proposal.get("description", ""),
                "recommendation": proposal.get("recommendation", ""),
                "type": proposal.get("type", "general"),
                "confidence": e.confidence,
                "evidence_count": proposal.get("evidence_count", 0),
                "status": proposal_status,
                "governance": meta.get("governance", "draft"),
                "icon": proposal.get("icon", "🧠"),
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "meta": meta,
            })
        
        return results

    @staticmethod
    def run_auto_scan(tenant_id: int, user_id: int) -> Dict:
        """Run a full scan and auto-propose patterns for high-confidence findings.
        
        This is the primary entry point for cron-based learning.
        """
        patterns = LearningEngine.scan_for_patterns(tenant_id)
        
        results = []
        for pattern in patterns:
            result = LearningEngine.propose(tenant_id, user_id, pattern)
            results.append({
                "title": pattern.get("title"),
                "confidence": pattern.get("confidence"),
                "proposed": result.success,
            })
        
        return {
            "patterns_found": len(patterns),
            "proposals_created": sum(1 for r in results if r["proposed"]),
            "results": results,
        }