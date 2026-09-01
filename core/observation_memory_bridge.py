"""Observation → Memory Bridge — closes the observation→memory loop.

Every time the execution chain creates or completes an observation, this
bridge persists it as a MemoryRecord so the Memory workspace can surface it
and the learning system can analyze patterns over time.

This bridges two canonical stores:
  - observations (execution outcomes, from core.execution_chain)
  - memory_records (durable knowledge, from app.memory.models)

The bridge is idempotent: the same observation_id always produces the same
memory_key, so re-running the bridge does not duplicate records.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from app import db

logger = logging.getLogger(__name__)


def observation_to_memory(
    observation_id: int,
    *,
    tenant_id: int | None = None,
    identity_id: str | None = None,
) -> bool:
    """Bridge a single observation into the memory_records table.

    Reads the observation from the DB and creates a corresponding
    MemoryRecord with the observation's content, status, and provenance.
    Idempotent — same observation_id always maps to the same memory_key.

    Returns True if a new memory record was created, False if it already
    existed or if the observation could not be read.
    """
    try:
        from app.shunya.observer_learning import Observation
        obs = db.session.get(Observation, observation_id)
        if not obs:
            logger.warning("observation_to_memory: observation %d not found", observation_id)
            return False

        # Build a deterministic memory key from the observation
        memory_key = _observation_memory_key(obs)

        # Check if already bridged
        from app.memory.models import MemoryRecord
        existing = MemoryRecord.query.filter_by(memory_key=memory_key).first()
        if existing:
            return False  # Already bridged — idempotent

        # Build the value from observation fields
        value_parts = []
        if obs.action:
            value_parts.append(f"Action: {obs.action}")
        if obs.actual_outcome:
            value_parts.append(f"Outcome: {obs.actual_outcome}")
        if obs.discrepancy:
            value_parts.append(f"Discrepancy: {obs.discrepancy}")
        outcome_text = "; ".join(value_parts) if value_parts else f"Observation #{observation_id}"

        # Determine memory type based on observation
        memory_type = "outcome"
        truth_classification = "observation"
        if obs.success is True:
            memory_type = "outcome"
            truth_classification = "observation"
        elif obs.success is False:
            memory_type = "outcome"
            truth_classification = "evidence"  # Failed outcomes are evidence of problems
        else:
            memory_type = "observation"
            truth_classification = "observation"

        record = MemoryRecord(
            tenant_id=obs.tenant_id or tenant_id,
            memory_type=memory_type,
            memory_key=memory_key,
            value=outcome_text[:2000],
            summary=f"{obs.action}: {obs.actual_outcome or ''}"[:500],
            scope_type="tenant",
            status="active",
            creation_mechanism="deterministic_derived",
            truth_classification=truth_classification,
            observed_at=obs.created_at,
            source_object_type="observation",
            source_object_id=obs.id,
            owner_identity_id=identity_id or "",
            source="execution_chain",
            created_by="observation_memory_bridge",
            confidence=float(obs.confidence) if obs.confidence else 1.0,
        )
        db.session.add(record)
        db.session.flush()

        # Add provenance linking back to the observation
        from app.memory.models import MemoryProvenance
        prov = MemoryProvenance(
            tenant_id=obs.tenant_id or tenant_id,
            memory_id=record.id,
            source_object_type="observation",
            source_object_id=obs.id,
            provenance_source="execution_chain",
            provenance_source_id=str(observation_id),
            provenance_role="source",
            creation_mechanism="deterministic_derived",
        )
        db.session.add(prov)
        db.session.commit()

        logger.info("Bridged observation %d → memory record %d (key=%s)",
                     observation_id, record.id, memory_key)
        return True

    except Exception as e:
        db.session.rollback()
        logger.warning("observation_to_memory failed for observation %d: %s",
                       observation_id, e)
        return False


def _observation_memory_key(obs: Any) -> str:
    """Build a deterministic memory key from an observation."""
    raw = f"obs_{obs.id}_{obs.action}_{obs.created_at}"
    return f"obs_{hashlib.md5(raw.encode()).hexdigest()[:16]}"


def bridge_pending_observations(*, tenant_id: int | None = None,
                                 identity_id: str | None = None) -> int:
    """Bridge all observations that have not yet been stored as memory.

    Scans observations that were created by the execution chain but have
    no corresponding memory record. Idempotent — safe to run repeatedly.

    Returns the count of newly bridged records.
    """
    count = 0
    try:
        from app.shunya.observer_learning import Observation
        from app.memory.models import MemoryRecord

        # Find all execution-chain observations
        obs_list = Observation.query.filter(
            Observation.source == "shunyaai",
            Observation.observer == "execution_chain",
        ).order_by(Observation.id.asc()).all()

        for obs in obs_list:
            memory_key = _observation_memory_key(obs)
            already = MemoryRecord.query.filter_by(memory_key=memory_key).first()
            if not already:
                if observation_to_memory(obs.id,
                                          tenant_id=tenant_id,
                                          identity_id=identity_id):
                    count += 1

        logger.info("Bridged %d pending observations", count)
    except Exception as e:
        logger.warning("bridge_pending_observations failed: %s", e)
    return count