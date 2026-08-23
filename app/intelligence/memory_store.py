def update_weight(key: str, delta: float) -> float:
    """Update the weight for a key by delta.

    Positive delta for success, negative for failure.
    Bounded between 0.15 (entropy floor) and 0.95 (ceiling).
    Decays toward 0.5 over time to prevent oscillation.
    Uses upsert (INSERT ... ON CONFLICT) for concurrent-safe idempotent writes.

    PHASE 3.4: Stability controls:
    - Entropy floor: 0.15 (never collapses to 0)
    - Ceiling: 0.95 (never explodes to 1)
    - Decay: weights drift back to 0.5 over time
    """
    try:
        entry = LearningWeight.query.filter_by(key=key).first()
        if entry:
            # Apply decay toward 0.5 (prevents runaway)
            decay_rate = 0.02
            if entry.weight > 0.5:
                entry.weight -= decay_rate
            elif entry.weight < 0.5:
                entry.weight += decay_rate

            entry.weight = max(0.15, min(0.95, entry.weight + delta))
            entry.sample_count = (entry.sample_count or 0) + 1
            entry.last_updated = now()
            get_session().flush()
            return entry.weight
        else:
            try:
                from sqlalchemy.dialects.postgresql import insert as pg_insert
                stmt = pg_insert(LearningWeight).values(
                    key=key,
                    weight=max(0.15, min(0.95, 0.5 + delta)),
                    sample_count=1,
                    last_updated=now(),
                )
                stmt = stmt.on_conflict_do_nothing(index_elements=["key"])
                get_session().execute(stmt)
            except Exception:
                try:
                    entry = LearningWeight(
                        key=key,
                        weight=max(0.15, min(0.95, 0.5 + delta)),
                        sample_count=1,
                    )
                    get_session().add(entry)
                except Exception:
                    pass
            try:
                get_session().flush()
            except Exception:
                get_session().rollback()
        return max(0.15, min(0.95, 0.5 + delta))
    except Exception as e:
        logger.debug("Could not update weight for %s: %s", key, e)
        return 0.5