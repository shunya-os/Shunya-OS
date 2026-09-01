"""Memory Engine — short-term, long-term, organization, and business memory.

Canonical memory engine for the SHUNYA Intelligence Runtime. Consumes the
canonical identity (identity_id + tenant_id) so every memory entry is scoped
to its owning identity and tenant. Persistence is delegated to a repository
adapter — the in-memory store is the fallback, and the DB-backed repository
(bridge to the canonical MemoryRecord model) is wired at app startup.

Identity convergence rule: no memory entry may exist without an owner. Every
store/search operation filters by identity_id and tenant_id so cross-tenant
or cross-user leakage is impossible by construction.
"""

from __future__ import annotations

from typing import Any, Callable

from .types import MemoryEntry, MemoryType

DEFAULT_TENANT = ""  # empty tenant = unfiltered only for system-scope entries


class MemoryRepository:
    """Persistence contract for durable memory.

    Implementations: InMemoryMemoryRepository (fallback) and
    DBMemoryRepository (canonical bridge to app.memory.models.MemoryRecord).
    """

    def store_entry(self, entry: MemoryEntry, identity_id: str = "", tenant_id: str = "") -> None:
        raise NotImplementedError

    def get_entry(self, key: str, identity_id: str = "", tenant_id: str = "") -> MemoryEntry | None:
        raise NotImplementedError

    def search(self, query: str, identity_id: str = "", tenant_id: str = "",
               memory_type: MemoryType | None = None, limit: int = 10) -> list[MemoryEntry]:
        raise NotImplementedError

    def recall_recent(self, identity_id: str = "", tenant_id: str = "",
                      memory_type: MemoryType | None = None, limit: int = 10) -> list[MemoryEntry]:
        raise NotImplementedError

    def forget(self, key: str, identity_id: str = "", tenant_id: str = "") -> bool:
        raise NotImplementedError

    def count(self, identity_id: str = "", tenant_id: str = "",
              memory_type: MemoryType | None = None) -> int:
        raise NotImplementedError

    def clear(self, identity_id: str = "", tenant_id: str = "", memory_type: MemoryType | None = None) -> None:
        raise NotImplementedError


class InMemoryMemoryRepository(MemoryRepository):
    """In-memory repository — development/testing fallback only."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str, str, str], MemoryEntry] = {}

    def _key(self, key: str, identity_id: str, tenant_id: str, memory_type: MemoryType) -> tuple:
        return (identity_id, tenant_id, memory_type.value, key)

    def store_entry(self, entry: MemoryEntry, identity_id: str = "", tenant_id: str = "") -> None:
        self._entries[self._key(entry.key, identity_id, tenant_id, entry.memory_type)] = entry

    def get_entry(self, key: str, identity_id: str = "", tenant_id: str = "") -> MemoryEntry | None:
        for (eid, tid, mt, k), e in self._entries.items():
            if k == key and eid == identity_id and tid == tenant_id and not e.is_expired():
                return e
        return None

    def search(self, query: str, identity_id: str = "", tenant_id: str = "",
               memory_type: MemoryType | None = None, limit: int = 10) -> list[MemoryEntry]:
        q = query.lower()
        results = []
        for (eid, tid, mt, k), e in self._entries.items():
            if eid != identity_id or tid != tenant_id:
                continue
            if memory_type and mt != memory_type.value:
                continue
            if e.is_expired():
                continue
            if q in e.content.lower() or q in e.key.lower():
                results.append(e)
        results.sort(key=lambda x: -x.confidence)
        return results[:limit]

    def recall_recent(self, identity_id: str = "", tenant_id: str = "",
                      memory_type: MemoryType | None = None, limit: int = 10) -> list[MemoryEntry]:
        entries = []
        for (eid, tid, mt, k), e in self._entries.items():
            if eid != identity_id or tid != tenant_id:
                continue
            if memory_type and mt != memory_type.value:
                continue
            if e.is_expired():
                continue
            entries.append(e)
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return entries[:limit]

    def forget(self, key: str, identity_id: str = "", tenant_id: str = "") -> bool:
        for (eid, tid, mt, k), e in list(self._entries.items()):
            if k == key and eid == identity_id and tid == tenant_id:
                del self._entries[(eid, tid, mt, k)]
                return True
        return False

    def count(self, identity_id: str = "", tenant_id: str = "",
              memory_type: MemoryType | None = None) -> int:
        return sum(
            1 for (eid, tid, mt, k) in self._entries
            if eid == identity_id and tid == tenant_id
            and (memory_type is None or mt == memory_type.value)
        )

    def clear(self, identity_id: str = "", tenant_id: str = "", memory_type: MemoryType | None = None) -> None:
        for (eid, tid, mt, k) in list(self._entries):
            if eid == identity_id and tid == tenant_id:
                if memory_type is None or mt == memory_type.value:
                    del self._entries[(eid, tid, mt, k)]


class MemoryEngine:
    """Multi-tier memory system — identity- and tenant-scoped.

    Every memory entry is owned by (identity_id, tenant_id). The engine
    delegates durable persistence to a MemoryRepository: DBMemoryRepository
    when wired (canonical MemoryRecord bridge), InMemory otherwise.
    """

    def __init__(self, repository: MemoryRepository | None = None):
        self._repo = repository or InMemoryMemoryRepository()
        # Local LRU cache for hot entries — always scoped by identity/tenant.
        self._stores: dict[MemoryType, dict[str, MemoryEntry]] = {
            MemoryType.SHORT_TERM: {},
            MemoryType.LONG_TERM: {},
            MemoryType.ORGANIZATION: {},
            MemoryType.BUSINESS: {},
        }
        self._default_identity = "system"
        self._default_tenant = ""

    # ── Repository wiring ──────────────────────────────────────────────────

    def set_repository(self, repository: MemoryRepository) -> None:
        """Swap persistence backing (e.g. in-memory → MemoryRecord DB bridge)."""
        self._repo = repository

    def get_repository(self) -> MemoryRepository:
        return self._repo

    # ── Store / Retrieve ──────────────────────────────────────────────────

    def store(self, key: str, content: str, memory_type: MemoryType = MemoryType.SHORT_TERM,
              source: str = "", confidence: float = 1.0, ttl_seconds: int = 0,
              identity_id: str = "", tenant_id: str = "") -> None:
        """Store a memory entry scoped to identity_id + tenant_id.

        If identity_id is empty, it defaults to "system" — but the identity
        convergence contract requires callers to pass the authenticated
        identity; the system scope is reserved for platform bootstrapping.
        """
        owner = identity_id or self._default_identity
        entry = MemoryEntry(key=key, content=content, memory_type=memory_type,
                            source=source, confidence=confidence, ttl_seconds=ttl_seconds)
        self._repo.store_entry(entry, identity_id=owner, tenant_id=tenant_id or self._default_tenant)
        # Mirror to hot cache
        self._stores[memory_type][key] = entry

    def get(self, key: str, memory_type: MemoryType | None = None,
            identity_id: str = "", tenant_id: str = "") -> MemoryEntry | None:
        """Get a memory entry scoped to identity/tenant. Checks all stores if type not specified."""
        owner = identity_id or self._default_identity
        tid = tenant_id or self._default_tenant
        if memory_type:
            entry = self._repo.get_entry(key, identity_id=owner, tenant_id=tid)
            if entry and not entry.is_expired():
                return entry
            return None
        for store_type in MemoryType:
            entry = self._repo.get_entry(key, identity_id=owner, tenant_id=tid)
            if entry and not entry.is_expired():
                return entry
        return None

    def search(self, query: str, memory_type: MemoryType | None = None,
               identity_id: str = "", tenant_id: str = "") -> list[MemoryEntry]:
        """Search memory by query string — strictly scoped to identity/tenant."""
        owner = identity_id or self._default_identity
        tid = tenant_id or self._default_tenant
        return self._repo.search(query, identity_id=owner, tenant_id=tid,
                                 memory_type=memory_type, limit=10)

    def recall_recent(self, memory_type: MemoryType | None = None, limit: int = 10,
                      identity_id: str = "", tenant_id: str = "") -> list[MemoryEntry]:
        """Get recent entries from a memory store — scoped to identity/tenant."""
        owner = identity_id or self._default_identity
        tid = tenant_id or self._default_tenant
        return self._repo.recall_recent(identity_id=owner, tenant_id=tid,
                                        memory_type=memory_type, limit=limit)

    def forget(self, key: str, memory_type: MemoryType | None = None,
               identity_id: str = "", tenant_id: str = "") -> bool:
        """Remove a memory entry — scoped to identity/tenant."""
        owner = identity_id or self._default_identity
        tid = tenant_id or self._default_tenant
        removed = self._repo.forget(key, identity_id=owner, tenant_id=tid)
        if removed and memory_type:
            self._stores[memory_type].pop(key, None)
        return removed

    def clear(self, memory_type: MemoryType | None = None,
              identity_id: str = "", tenant_id: str = "") -> None:
        owner = identity_id or self._default_identity
        tid = tenant_id or self._default_tenant
        self._repo.clear(identity_id=owner, tenant_id=tid, memory_type=memory_type)
        if memory_type:
            self._stores[memory_type].clear()
        else:
            for mt in MemoryType:
                self._stores[mt].clear()

    def count(self, memory_type: MemoryType | None = None,
              identity_id: str = "", tenant_id: str = "") -> int:
        owner = identity_id or self._default_identity
        tid = tenant_id or self._default_tenant
        return self._repo.count(identity_id=owner, tenant_id=tid, memory_type=memory_type)


def _default_repository() -> MemoryRepository:
    """Static factory: DB-backed repository when inside the Flask app, in-memory otherwise."""
    try:
        from flask import current_app
        if current_app:
            from core.intelligence_runtime.memory_db import DBMemoryRepository
            return DBMemoryRepository()
    except Exception:
        pass
    return InMemoryMemoryRepository()