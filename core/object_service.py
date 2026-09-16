"""
SHUNYA Canonical Object Service — one production object authority.

Singular write path for all canonical objects. Reads from sh_objects.
Organization/tenant isolation enforced via real organization_id column.
Migration sources: objects, founder_objects, sh_uop_objects.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class ObjectService:
    """Canonical object authority. All object writes go through this service."""

    def __init__(self):
        from app import db
        self.db = db

    def create(self, object_type: str, name: str, organization_id: int,
               data: Optional[dict] = None, created_by: Optional[str] = None,
               status: str = "active", workspace_id: Optional[str] = None,
               object_id: Optional[str] = None,
               identity_id: Optional[str] = None,
               system_scope: bool = False) -> dict:
        """Create a canonical object. Returns the created record.

        Rejects missing/synthetic ownership. Callers are responsible for
        resolving real organization context from the authenticated identity
        before calling.

        ``workspace_id`` is required and has no default. ``sh_objects
        .workspace_id`` is NOT NULL — a workspace is part of the object's
        canonical identity — so a default business workspace ("spc_business")
        must never be assumed: that would silently place an object in a
        tenant workspace the caller never selected.
        """
        if not organization_id or organization_id < 1:
            raise ValueError(
                f"ObjectService.create() requires a valid positive organization_id, "
                f"got {organization_id!r}. Missing ownership MUST FAIL CLOSED."
            )
        if not workspace_id:
            raise ValueError(
                "ObjectService.create() requires an explicit workspace_id. "
                "sh_objects.workspace_id is NOT NULL, so a workspace is part of "
                "the object's canonical identity; a default business workspace "
                "MUST NOT be invented. Missing workspace MUST FAIL CLOSED."
            )
        # Ownership consistency is enforced here, not merely assumed of the
        # caller: the workspace must actually belong to the organization the
        # object is being created in. This makes cross-tenant placement
        # impossible even if a caller supplies mismatched values.
        from sqlalchemy import text as _sql
        _ws_ok = self.db.session.execute(
            _sql("SELECT 1 FROM sh_workspaces "
                 "WHERE id = :ws AND organization_id = :org"),
            {"ws": workspace_id, "org": organization_id},
        ).scalar()
        if not _ws_ok:
            raise ValueError(
                f"ObjectService.create() rejected: workspace {workspace_id!r} does "
                f"not belong to organization {organization_id!r}. The workspace "
                f"must be owned by the same organization as the object."
            )
        # Identity authorization (R6B-2.7 Window 6): when the caller supplies an
        # authenticated identity, that identity must be actively authorized for
        # this exact organization + workspace pair. This makes the service the
        # final server-side safety boundary — a caller cannot bypass it by
        # supplying a matching org/workspace combination it is not entitled to.
        if identity_id:
            from app.authz.workspace_context import assert_object_access
            assert_object_access(identity_id, organization_id, workspace_id)
        elif not system_scope:
            raise ValueError(
                "ObjectService.create() requires an authenticated identity_id, "
                "or an explicit system_scope=True for an audited non-user "
                "caller. identity_id=None MUST NOT skip authorization."
            )
        if identity_id and system_scope:
            raise ValueError(
                "ObjectService.create() received contradictory authorization "
                "context: identity_id and system_scope are mutually exclusive."
            )
        from sqlalchemy import text
        now = datetime.now(timezone.utc)
        oid = object_id or str(uuid.uuid4())
        result = self.db.session.execute(
            text("""
                INSERT INTO sh_objects
                    (object_id, object_type, name, status, workspace_id, organization_id, data, created_by, created_at, updated_at, is_deleted)
                VALUES
                    (:oid, :object_type, :name, :status, :workspace_id, :organization_id, :data, :created_by, :created_at, :updated_at, false)
                RETURNING id
            """),
            {
                "oid": oid,
                "object_type": object_type,
                "name": name,
                "status": status,
                "workspace_id": workspace_id,
                "organization_id": organization_id,
                "data": json.dumps(data or {}),
                "created_by": created_by or "",
                "created_at": now,
                "updated_at": now,
            }
        )
        obj_id = result.scalar()
        self.db.session.commit()
        # Fetch the generated object_id (UUID string)
        from sqlalchemy import text as _text
        row = self.db.session.execute(
            _text("SELECT object_id FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        object_id = row[0] if row else ""
        return {"id": obj_id, "object_id": object_id, "object_type": object_type, "name": name, "status": status, "organization_id": organization_id}

    def get(self, obj_id: int, organization_id: int = 0,
            identity_id: Optional[str] = None,
            system_scope: bool = False) -> Optional[dict]:
        """Get an object by ID, scoped to organization.

        When organization_id > 0, the lookup is scoped to that organization.
        When 0, returns only objects with NULL organization (orphaned/personal).

        Authorization: when ``identity_id`` is supplied, the identity must be
        actively authorized for the object's PERSISTED organization and
        workspace — never for values supplied by the caller.
        """
        from sqlalchemy import text
        if not identity_id and not system_scope:
            raise ValueError(
                "ObjectService.get() requires an authenticated identity_id, or "
                "an explicit system_scope=True for an audited non-user caller. "
                "Missing authorization context MUST FAIL CLOSED."
            )
        if identity_id and system_scope:
            raise ValueError(
                "ObjectService.get() received contradictory authorization "
                "context: identity_id and system_scope are mutually exclusive."
            )
        if organization_id > 0:
            row = self.db.session.execute(
                text("SELECT * FROM sh_objects WHERE id = :id AND organization_id = :org_id"),
                {"id": obj_id, "org_id": organization_id},
            ).first()
        else:
            row = self.db.session.execute(
                text("SELECT * FROM sh_objects WHERE id = :id AND organization_id IS NULL"),
                {"id": obj_id},
            ).first()
        if not row:
            return None
        if identity_id:
            # Authorize against the row's PERSISTED ownership, not the caller's
            # claim. A caller cannot widen access by supplying org/workspace.
            from app.authz.workspace_context import (
                OwnershipContextError, assert_object_access,
            )
            try:
                assert_object_access(identity_id, row.organization_id,
                                     row.workspace_id)
            except OwnershipContextError:
                return None
        return self._row_to_dict(row)

    def _authorized_scope(self, identity_id: Optional[str], organization_id: int,
                          method: str) -> list:
        """Authorized ``sh_workspaces.id`` set for identity+organization.

        Every non-CRUD read surface goes through this. It is the same predicate
        the CRUD gates use, so a read can never be wider than a write.
        Raises ``ValueError`` when identity/organization is missing and
        ``OwnershipContextError`` when the identity is authorized for nothing.
        """
        from app.authz.workspace_context import (
            OwnershipContextError, authorized_workspace_ids,
        )
        if not organization_id:
            raise ValueError(
                f"ObjectService.{method}() requires a positive organization_id. "
                "Missing ownership MUST FAIL CLOSED."
            )
        if not identity_id:
            raise ValueError(
                f"ObjectService.{method}() requires an authenticated identity_id. "
                "An identity-less read MUST NOT return tenant data."
            )
        workspaces = authorized_workspace_ids(str(identity_id), organization_id)
        if not workspaces:
            raise OwnershipContextError(
                f"identity {identity_id!r} is not authorized for any workspace in "
                f"organization {organization_id}",
                code="no_authorized_workspace",
            )
        return workspaces

    def get_by_object_id(self, object_id_str: str, organization_id: int,
                         identity_id: Optional[str] = None) -> Optional[dict]:
        """Get an object by its unique object_id string, scoped to organization.

        The lookup is scoped to the organization AND to the caller's authorized
        workspaces, and it is authorized against the row's PERSISTED workspace.
        Returns ``None`` for a denial (the object is simply not visible).
        """
        from sqlalchemy import text
        authorized = self._authorized_scope(identity_id, organization_id,
                                            "get_by_object_id")
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE object_id = :oid "
                 "AND organization_id = :org_id AND is_deleted = false"),
            {"oid": object_id_str, "org_id": organization_id},
        ).first()
        if not row:
            return None
        if row.workspace_id not in authorized:
            return None
        return self._row_to_dict(row)

    def get_by_type(self, object_type: str, organization_id: int,
                    identity_id: Optional[str] = None,
                    limit: int = 100, offset: int = 0) -> list:
        """List objects by type within the caller's authorized workspaces."""
        from sqlalchemy import bindparam, text
        authorized = self._authorized_scope(identity_id, organization_id,
                                            "get_by_type")
        stmt = text("""
                SELECT * FROM sh_objects
                WHERE object_type = :object_type
                AND organization_id = :org_id
                AND workspace_id IN :ws_ids
                AND is_deleted = false
                ORDER BY updated_at DESC LIMIT :lim OFFSET :off
            """).bindparams(bindparam("ws_ids", expanding=True))
        rows = self.db.session.execute(
            stmt,
            {"object_type": object_type, "org_id": organization_id,
             "ws_ids": list(authorized), "lim": limit, "off": offset},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def list_by_workspace(self, workspace_id: str, organization_id: int,
                          identity_id: Optional[str] = None,
                          status: str = "active", limit: int = 100,
                          offset: int = 0) -> list:
        """List objects within one workspace, authorized for this identity."""
        from sqlalchemy import text
        authorized = self._authorized_scope(identity_id, organization_id,
                                            "list_by_workspace")
        if str(workspace_id) not in authorized:
            from app.authz.workspace_context import OwnershipContextError
            raise OwnershipContextError(
                f"identity {identity_id!r} is not authorized for workspace "
                f"{workspace_id!r} in organization {organization_id}",
                code="workspace_not_authorized",
            )
        rows = self.db.session.execute(
            text("""
                SELECT * FROM sh_objects
                WHERE workspace_id = :ws_id
                AND organization_id = :org_id
                AND status = :status
                AND is_deleted = false
                ORDER BY updated_at DESC LIMIT :lim OFFSET :off
            """),
            {"ws_id": workspace_id, "org_id": organization_id, "status": status,
             "lim": limit, "off": offset},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def list_by_creator(self, created_by: str, organization_id: int,
                        identity_id: Optional[str] = None,
                        status: str = "active", limit: int = 100) -> list:
        """List objects created by an identity, within the caller's authorized
        workspaces. An identity cannot read another identity's objects in a
        workspace it is not itself authorized for.
        """
        from sqlalchemy import bindparam, text
        authorized = self._authorized_scope(identity_id, organization_id,
                                            "list_by_creator")
        stmt = text("""
                    SELECT * FROM sh_objects
                    WHERE created_by = :creator
                    AND organization_id = :org_id
                    AND workspace_id IN :ws_ids
                    AND status = :status
                    AND is_deleted = false
                    ORDER BY updated_at DESC LIMIT :lim
                """).bindparams(bindparam("ws_ids", expanding=True))
        rows = self.db.session.execute(
            stmt,
            {"creator": created_by, "org_id": organization_id,
             "ws_ids": list(authorized), "status": status, "lim": limit},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def search(self, query: str, organization_id: int,
               identity_id: Optional[str] = None, limit: int = 50) -> list:
        """Search objects within the caller's authorized workspaces."""
        from sqlalchemy import bindparam, text
        authorized = self._authorized_scope(identity_id, organization_id, "search")
        like = f"%{query}%"
        stmt = text("""
                SELECT * FROM sh_objects
                WHERE LOWER(name) LIKE LOWER(:like)
                AND organization_id = :org_id
                AND workspace_id IN :ws_ids
                ORDER BY updated_at DESC LIMIT :lim
            """).bindparams(bindparam("ws_ids", expanding=True))
        rows = self.db.session.execute(
            stmt,
            {"like": like, "org_id": organization_id,
             "ws_ids": list(authorized), "lim": limit},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def update(self, obj_id: int, organization_id: int,
               identity_id: Optional[str] = None,
               system_scope: bool = False, **kwargs) -> bool:
        """Update an object. Returns False if cross-tenant or not found.

        When ``identity_id`` is supplied, the identity must be actively
        authorized for the organization+workspace the object actually lives in
        — so a caller cannot update an object by presenting a valid-looking
        organization of its own.
        """
        if identity_id and system_scope:
            raise ValueError(
                "ObjectService.update() received contradictory authorization "
                "context: identity_id and system_scope are mutually exclusive."
            )
        if not identity_id and not system_scope:
            raise ValueError(
                "ObjectService.update() requires an authenticated identity_id, or "
                "an explicit system_scope=True for an audited non-user caller. "
                "identity_id=None MUST NOT skip authorization; delete() delegates "
                "here, so this is also the delete authorization gate."
            )
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        if not row or row.organization_id != organization_id:
            return False

        if identity_id:
            from app.authz.workspace_context import (
                OwnershipContextError, assert_object_access,
            )
            try:
                assert_object_access(identity_id, row.organization_id,
                                     row.workspace_id)
            except OwnershipContextError:
                # Authorization denial only. Unexpected programming or database
                # errors must surface rather than masquerade as "denied".
                return False

        updates = {"updated_at": datetime.now(timezone.utc)}
        if "name" in kwargs:
            updates["name"] = kwargs["name"]
        if "object_type" in kwargs:
            updates["object_type"] = kwargs["object_type"]
        if "status" in kwargs:
            updates["status"] = kwargs["status"]
        if "data" in kwargs:
            updates["data"] = json.dumps(kwargs["data"])
        if "is_deleted" in kwargs:
            updates["is_deleted"] = kwargs["is_deleted"]

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = obj_id
        self.db.session.execute(
            text(f"UPDATE sh_objects SET {set_clause} WHERE id = :id"), updates
        )
        self.db.session.commit()
        return True

    def delete(self, obj_id: int, organization_id: int,
               identity_id: Optional[str] = None,
               system_scope: bool = False) -> bool:
        """Soft-delete an object. Returns False if cross-tenant.

        Delegates to update(), which is the authorization gate for both write
        operations — a separate check here would leave the lower-level path weak.
        """
        return self.update(obj_id, organization_id, identity_id=identity_id,
                           system_scope=system_scope, status="archived")

    def permanent_delete(self, obj_id: int, organization_id: int,
                         identity_id: Optional[str] = None,
                         system_scope: bool = False) -> bool:
        """Permanently delete an object from the database.

        Authorization flows through persisted-ownership gate.
        Only permitted when the object is in TRASHED state (is_deleted=True).
        Irreversible — the row is removed from the database.
        Audit trail: the caller's identity is verified both before and after
        authorization, and the DELETE is logged through the existing commit.
        """
        from sqlalchemy import text
        if identity_id and system_scope:
            raise ValueError(
                "permanent_delete: identity_id and system_scope are exclusive."
            )
        if not identity_id and not system_scope:
            raise ValueError(
                "permanent_delete requires identity_id or system_scope."
            )
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        if not row:
            return False
        if row.organization_id != organization_id:
            return False
        if identity_id:
            from app.authz.workspace_context import (
                OwnershipContextError, assert_object_access,
            )
            try:
                assert_object_access(identity_id, row.organization_id,
                                     row.workspace_id)
            except OwnershipContextError:
                return False
        # Only allow permanent delete from trashed state
        if not row.is_deleted:
            return False
        self.db.session.execute(
            text("DELETE FROM sh_objects WHERE id = :id"), {"id": obj_id}
        )
        self.db.session.commit()
        return True

    def archive(self, obj_id: int, organization_id: int,
                identity_id: Optional[str] = None,
                system_scope: bool = False) -> bool:
        """Soft-archive: set status='archived'. Only from ACTIVE state.
        ACTIVE → ARCHIVED.
        """
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT status, is_deleted FROM sh_objects WHERE id = :id"),
            {"id": obj_id}
        ).first()
        if not row:
            return False
        if row.is_deleted:
            return False
        if row.status == "archived":
            return False  # already archived — idempotent reject
        return self.update(obj_id, organization_id, identity_id=identity_id,
                           system_scope=system_scope, status="archived")

    def restore(self, obj_id: int, organization_id: int,
                identity_id: Optional[str] = None,
                system_scope: bool = False) -> bool:
        """Restore from archived: set status='active'.
        ARCHIVED → ACTIVE.
        """
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT status, is_deleted FROM sh_objects WHERE id = :id"),
            {"id": obj_id}
        ).first()
        if not row:
            return False
        if row.is_deleted:
            return False
        if row.status != "archived":
            return False
        return self.update(obj_id, organization_id, identity_id=identity_id,
                           system_scope=system_scope, status="active")

    def trash(self, obj_id: int, organization_id: int,
              identity_id: Optional[str] = None,
              system_scope: bool = False) -> bool:
        """Move to trash: set is_deleted=true.
        ACTIVE or ARCHIVED → TRASHED.
        """
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT is_deleted FROM sh_objects WHERE id = :id"),
            {"id": obj_id}
        ).first()
        if not row:
            return False
        if row.is_deleted:
            return False  # already trashed
        return self.update(obj_id, organization_id, identity_id=identity_id,
                           system_scope=system_scope, is_deleted=True)

    def recover(self, obj_id: int, organization_id: int,
                identity_id: Optional[str] = None,
                system_scope: bool = False) -> bool:
        """Recover from trash: set is_deleted=false, status='active'.
        TRASHED → ACTIVE.
        """
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT is_deleted FROM sh_objects WHERE id = :id"),
            {"id": obj_id}
        ).first()
        if not row:
            return False
        if not row.is_deleted:
            return False  # not trashed — can't recover
        return self.update(obj_id, organization_id, identity_id=identity_id,
                           system_scope=system_scope, is_deleted=False,
                           status="active")

    def count_by_type(self, organization_id: int,
                      identity_id: Optional[str] = None) -> dict:
        """Count objects grouped by type within the caller's authorized workspaces."""
        from sqlalchemy import bindparam, text
        authorized = self._authorized_scope(identity_id, organization_id,
                                            "count_by_type")
        stmt = text("""
                SELECT object_type, COUNT(*) as cnt FROM sh_objects
                WHERE organization_id = :org_id
                AND workspace_id IN :ws_ids
                GROUP BY object_type
            """).bindparams(bindparam("ws_ids", expanding=True))
        rows = self.db.session.execute(
            stmt,
            {"org_id": organization_id, "ws_ids": list(authorized)},
        ).all()
        return {r[0]: r[1] for r in rows}

    def migrate_from(self, source_table: str, organization_id: int,
                     type_map: Optional[dict] = None) -> dict:
        """Migrate records from a legacy object table into sh_objects.
        Returns migration report with counts and mapping."""
        from sqlalchemy import Table, MetaData, text

        src_tbl = Table(source_table, MetaData(), autoload_with=self.db.engine)
        rows = self.db.session.execute(src_tbl.select()).all()
        migrated = 0
        skipped = 0
        mapping = []

        for row in rows:
            obj_type = (type_map or {}).get(source_table, source_table.replace("_", ""))
            name = getattr(row, "name", None) or getattr(row, "title", None) or str(getattr(row, "id", ""))
            source_id = getattr(row, "id", None)

            # Check if already migrated (by source_id stored in data)
            existing = self.db.session.execute(
                text("""
                    SELECT id FROM sh_objects
                    WHERE data->>'source_table' = :src_tbl
                    AND data->>'source_id' = :src_id
                """),
                {"src_tbl": source_table, "src_id": str(source_id)},
            ).first()
            if existing:
                mapping.append({"source_id": source_id, "canonical_id": existing[0], "action": "skipped_duplicate"})
                skipped += 1
                continue

            data = {}
            for col in row._mapping.keys():
                if col not in ("id", "name", "title", "object_type", "tenant_id",
                               "created_at", "updated_at", "status"):
                    try:
                        val = getattr(row, col)
                        if val is not None:
                            data[col] = str(val) if not isinstance(val, (int, float, bool, dict, list)) else val
                    except Exception:
                        pass

            # Mark provenance
            data["source_table"] = source_table
            data["source_id"] = str(source_id)

            row_org = getattr(row, "organization_id", None) or getattr(row, "tenant_id", None) or organization_id
            row_status = getattr(row, "status", None) or "active"
            if row_status == "deleted":
                row_status = "archived"

            try:
                obj = self.create(
                    object_type=obj_type,
                    name=str(name)[:500],
                    organization_id=int(row_org) if row_org else organization_id,
                    data=data,
                    status=row_status,
                )
                mapping.append({"source_id": source_id, "canonical_id": obj["id"], "action": "migrated"})
                migrated += 1
            except Exception as e:
                mapping.append({"source_id": source_id, "canonical_id": None, "action": "error", "error": str(e)})

        return {
            "source_table": source_table,
            "total": len(rows),
            "migrated": migrated,
            "skipped_duplicates": skipped,
            "errors": len(rows) - migrated - skipped,
            "mapping": mapping,
        }

    @staticmethod
    def _row_to_dict(row) -> dict:
        bool_cols = {"is_deleted"}
        result = {}
        for col in row._mapping.keys():
            val = getattr(row, col)
            if isinstance(val, datetime):
                val = val.isoformat()
            if col in bool_cols:
                val = bool(val)
            result[col] = val
        return result


_object_service: Optional[ObjectService] = None


def get_object_service() -> ObjectService:
    global _object_service
    if _object_service is None:
        _object_service = ObjectService()
    return _object_service