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
               status: str = "active", workspace_id: str = "spc_business") -> dict:
        """Create a canonical object. Returns the created record."""
        from sqlalchemy import text
        now = datetime.now(timezone.utc)
        result = self.db.session.execute(
            text("""
                INSERT INTO sh_objects
                    (object_id, object_type, name, status, workspace_id, organization_id, data, created_by, created_at, updated_at)
                VALUES
                    (:oid, :object_type, :name, :status, :workspace_id, :organization_id, :data, :created_by, :created_at, :updated_at)
                RETURNING id
            """),
            {
                "oid": str(uuid.uuid4()),
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
        self.db.session.commit()
        obj_id = result.scalar()
        # Also fetch the generated object_id (UUID string)
        from sqlalchemy import text as _text
        row = self.db.session.execute(
            _text("SELECT object_id FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        object_id = row[0] if row else ""
        return {"id": obj_id, "object_id": object_id, "object_type": object_type, "name": name, "status": status, "organization_id": organization_id}

    def get(self, obj_id: int) -> Optional[dict]:
        """Get an object by ID."""
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        if not row:
            return None
        return self._row_to_dict(row)

    def get_by_type(self, object_type: str, organization_id: int,
                    limit: int = 100, offset: int = 0) -> list:
        """List objects by type within an organization."""
        from sqlalchemy import text
        rows = self.db.session.execute(
            text("""
                SELECT * FROM sh_objects
                WHERE object_type = :object_type
                AND organization_id = :org_id
                ORDER BY updated_at DESC LIMIT :lim OFFSET :off
            """),
            {"object_type": object_type, "org_id": organization_id, "lim": limit, "off": offset},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def search(self, query: str, organization_id: int, limit: int = 50) -> list:
        """Search objects by name/type within an organization."""
        from sqlalchemy import text
        like = f"%{query}%"
        rows = self.db.session.execute(
            text("""
                SELECT * FROM sh_objects
                WHERE name ILIKE :like
                AND organization_id = :org_id
                ORDER BY updated_at DESC LIMIT :lim
            """),
            {"like": like, "org_id": organization_id, "lim": limit},
        ).all()
        return [self._row_to_dict(r) for r in rows]

    def update(self, obj_id: int, organization_id: int, **kwargs) -> bool:
        """Update an object. Returns False if cross-tenant or not found."""
        from sqlalchemy import text
        row = self.db.session.execute(
            text("SELECT * FROM sh_objects WHERE id = :id"), {"id": obj_id}
        ).first()
        if not row or row.organization_id != organization_id:
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

        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = obj_id
        self.db.session.execute(
            text(f"UPDATE sh_objects SET {set_clause} WHERE id = :id"), updates
        )
        self.db.session.commit()
        return True

    def delete(self, obj_id: int, organization_id: int) -> bool:
        """Soft-delete an object. Returns False if cross-tenant."""
        return self.update(obj_id, organization_id, status="archived")

    def count_by_type(self, organization_id: int) -> dict:
        """Count objects grouped by type within an organization."""
        from sqlalchemy import text
        rows = self.db.session.execute(
            text("""
                SELECT object_type, COUNT(*) as cnt FROM sh_objects
                WHERE organization_id = :org_id
                GROUP BY object_type
            """),
            {"org_id": organization_id},
        ).all()
        return {r[0]: r[1] for r in rows}

    def migrate_from(self, source_table: str, organization_id: int = 1,
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