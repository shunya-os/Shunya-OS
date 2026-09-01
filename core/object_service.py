"""
SHUNYA Canonical Object Service — one production object authority.

Singular write path for all canonical objects. Reads from sh_objects.
Migration sources: objects, founder_objects, sh_uop_objects.
Tenant isolation is enforced via data->>'organization_id' in JSONB.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from flask import session, g

logger = logging.getLogger(__name__)


class ObjectService:
    """Canonical object authority. All object writes go through this service."""

    def __init__(self):
        from app import db
        self.db = db

    def create(self, object_type: str, name: str, tenant_id: int,
               data: Optional[dict] = None, created_by: Optional[str] = None,
               status: str = "active", workspace_id: str = "spc_business") -> dict:
        """Create a canonical object. Returns the created record."""
        from sqlalchemy import text
        now = datetime.now(timezone.utc)
        payload = dict(data or {})
        payload["organization_id"] = tenant_id
        result = self.db.session.execute(
            text("""
                INSERT INTO sh_objects (object_id, object_type, name, status, workspace_id, data, created_by, created_at, updated_at)
                VALUES (:oid, :object_type, :name, :status, :workspace_id, :data, :created_by, :created_at, :updated_at)
                RETURNING id
            """),
            {
                "oid": str(uuid.uuid4()),
                "object_type": object_type,
                "name": name,
                "status": status,
                "workspace_id": workspace_id,
                "data": json.dumps(payload),
                "created_by": created_by or "",
                "created_at": now,
                "updated_at": now,
            }
        )
        self.db.session.commit()
        obj_id = result.scalar()
        return {"id": obj_id, "object_type": object_type, "name": name, "status": status}

    def get(self, obj_id: int) -> Optional[dict]:
        """Get an object by ID."""
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        if not row:
            return None
        return self._row_to_dict(row)

    def get_by_type(self, object_type: str, tenant_id: int,
                    limit: int = 100, offset: int = 0) -> list:
        """List objects by type within a tenant."""
        from sqlalchemy import text
        rows = self.db.session.execute(
            text("""
                SELECT * FROM sh_objects
                WHERE object_type = :object_type
                AND data->>'organization_id' = :org_id
                ORDER BY updated_at DESC LIMIT :lim OFFSET :off
            """),
            {"object_type": object_type, "org_id": str(tenant_id), "lim": limit, "off": offset},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def search(self, query: str, tenant_id: int, limit: int = 50) -> list:
        """Search objects by name/type within a tenant."""
        from sqlalchemy import text
        like = f"%{query}%"
        rows = self.db.session.execute(
            text("""
                SELECT * FROM sh_objects
                WHERE name ILIKE :like
                AND data->>'organization_id' = :org_id
                ORDER BY updated_at DESC LIMIT :lim
            """),
            {"like": like, "org_id": str(tenant_id), "lim": limit},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def update(self, obj_id: int, tenant_id: int, **kwargs) -> bool:
        """Update an object. Returns False if cross-tenant or not found."""
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        if not row:
            return False
        # Check tenant isolation via data JSONB
        row_data = json.loads(row.data) if isinstance(row.data, str) else (row.data or {})
        if str(row_data.get("organization_id", "")) != str(tenant_id):
            return False

        updates = {"updated_at": datetime.now(timezone.utc)}
        if "name" in kwargs:
            updates["name"] = kwargs["name"]
        if "object_type" in kwargs:
            updates["object_type"] = kwargs["object_type"]
        if "status" in kwargs:
            updates["status"] = kwargs["status"]
        if "data" in kwargs:
            payload = dict(kwargs["data"])
            payload["organization_id"] = tenant_id
            updates["data"] = json.dumps(payload)

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = obj_id
        self.db.session.execute(
            text(f"UPDATE sh_objects SET {set_clause} WHERE id = :id"), updates
        )
        self.db.session.commit()
        return True

    def delete(self, obj_id: int, tenant_id: int) -> bool:
        """Soft-delete an object (set status=archived). Returns False if cross-tenant."""
        return self.update(obj_id, tenant_id, status="archived")

    def count_by_type(self, tenant_id: int) -> dict:
        """Count objects grouped by type within a tenant."""
        from sqlalchemy import text
        rows = self.db.session.execute(
            text("""
                SELECT object_type, COUNT(*) as cnt FROM sh_objects
                WHERE data->>'organization_id' = :org_id
                GROUP BY object_type
            """),
            {"org_id": str(tenant_id)},
        ).all()
        return {r[0]: r[1] for r in rows}

    def migrate_from(self, source_table: str, target_tenant_id: int = 1,
                     type_map: Optional[dict] = None) -> int:
        """Migrate records from a legacy object table into sh_objects.
        Returns count of migrated records."""
        from sqlalchemy import Table, MetaData, text

        src_tbl = Table(source_table, MetaData(), autoload_with=self.db.engine)
        rows = self.db.session.execute(src_tbl.select()).all()
        migrated = 0
        for row in rows:
            obj_type = (type_map or {}).get(source_table, source_table.replace("_", ""))
            name = getattr(row, "name", None) or getattr(row, "title", None) or str(getattr(row, "id", ""))
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

            row_tenant = getattr(row, "tenant_id", None) or target_tenant_id
            row_status = getattr(row, "status", None) or "active"
            if row_status == "deleted":
                row_status = "archived"

            self.create(
                object_type=obj_type,
                name=str(name)[:500],
                tenant_id=int(row_tenant) if row_tenant else target_tenant_id,
                data=data,
                status=row_status,
            )
            migrated += 1
        return migrated

    @staticmethod
    def _row_to_dict(row) -> dict:
        result = {}
        for col in row._mapping.keys():
            val = getattr(row, col)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col] = val
        return result


_object_service: Optional[ObjectService] = None


def get_object_service() -> ObjectService:
    global _object_service
    if _object_service is None:
        _object_service = ObjectService()
    return _object_service