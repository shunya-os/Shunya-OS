"""
SHUNYA — Data Migration Engine (M2C.5R Deliverable)

Deterministic, idempotent, auditable data migration framework for
converging legacy records into canonical stores.

Architecture:
  MigrationPlan
    ├── SourceDefinition  (what, where, how to query)
    ├── TargetMapping     (canonical table, column mapping, ID generation)
    ├── MigrationLedger   (records what was migrated, rollback info)
    └── Engine            (dry-run, execute, rollback, reconcile)

Usage:
  engine = MigrationEngine()
  plan = MigrationPlan.define(
      name="objects_v2",
      source_query="SELECT * FROM sh_uop_objects WHERE ...",
      target_store=canonical_store,
      identity_fn=lambda row: deterministic_hash(row),
  )
  report = engine.dry_run(plan)       # No mutations
  report = engine.preflight(plan)     # Verify prerequisites
  report = engine.execute(plan)       # Transactional, ledgered
  report = engine.reconcile(plan)     # Verify all records arrived
  report = engine.rollback(plan)      # Rollback via ledger
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from app import db

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# Types
# ═══════════════════════════════════════════════════════════════════════


class MigrationStatus(Enum):
    PENDING = "pending"
    DRY_RUN = "dry_run"
    PREFLIGHT_PASS = "preflight_pass"
    PREFLIGHT_FAIL = "preflight_fail"
    EXECUTING = "executing"
    COMMITTED = "committed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    RECONCILED = "reconciled"
    RECONCILE_FAIL = "reconcile_fail"


@dataclass
class MigrationRecord:
    """One migrated record — source identity → canonical identity."""
    migration_id: str
    batch_id: str
    source_table: str
    source_pk: str
    source_pk_value: str
    source_tenant_id: Optional[int]
    canonical_table: str
    canonical_pk_value: str
    target_tenant_id: Optional[int]
    identity_hash: str       # deterministic hash of source fields
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    rolled_back_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class MigrationBatch:
    """One batch execution."""
    batch_id: str
    plan_name: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "pending"
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    backup_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SourceDefinition:
    """Defines a source data set to migrate."""
    table_name: str
    query: str                     # SQL or query expression
    pk_column: str                 # Primary key column name
    tenant_column: Optional[str] = None   # Column holding tenant_id (if any)
    identity_fields: list[str] = field(default_factory=list)     # Fields that determine identity
    order_by: Optional[str] = None
    limit: Optional[int] = None
    where_clause: Optional[str] = None


@dataclass
class TargetMapping:
    """Defines how source maps to canonical target."""
    table_name: str                # Canonical target table
    pk_column: str                 # Canonical PK column
    identity_field: str            # Target field for deterministic ID
    tenant_column: Optional[str] = None   # Tenant column in target
    field_map: dict[str, str] = field(default_factory=dict)      # source_field -> target_field
    extra_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreflightCheck:
    name: str
    passed: bool
    detail: str


@dataclass
class MigrationPlan:
    """Complete definition of one migration."""
    name: str
    description: str
    source: SourceDefinition
    target: TargetMapping
    identity_fn: Callable[[dict], str]    # Deterministic hash per record
    tenant_resolver: Optional[Callable[[dict], int]] = None
    on_conflict: str = "skip"             # skip | overwrite | raise


@dataclass
class MigrationReport:
    """Result of a migration operation."""
    plan_name: str
    operation: str               # dry_run | preflight | execute | reconcile | rollback
    status: MigrationStatus
    started_at: str
    completed_at: Optional[str] = None
    batch: Optional[MigrationBatch] = None
    records: list[MigrationRecord] = field(default_factory=list)
    preflight_checks: list[PreflightCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# Ledger (persistence layer)
# ═══════════════════════════════════════════════════════════════════════


MIGRATION_LEDGER = []   # In-memory ledger for this session


def _log_to_ledger(record: MigrationRecord):
    """Persist a migration record to the ledger."""
    MIGRATION_LEDGER.append(record)
    # TODO: persist to migration_ledger table when implemented


def _find_ledger_entry(identity_hash: str) -> Optional[MigrationRecord]:
    """Find existing migration by identity hash."""
    for r in reversed(MIGRATION_LEDGER):
        if r.identity_hash == identity_hash and r.status == "committed":
            return r
    return None


# ═══════════════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════════════


class MigrationEngine:
    """Deterministic, idempotent data migration engine."""

    def __init__(self):
        self._plans: dict[str, MigrationPlan] = {}

    def register(self, plan: MigrationPlan):
        if plan.name in self._plans:
            raise ValueError(f"Plan '{plan.name}' already registered")
        self._plans[plan.name] = plan

    def get(self, name: str) -> Optional[MigrationPlan]:
        return self._plans.get(name)

    # ── Dry Run ──────────────────────────────────────────────────────

    def dry_run(self, plan: MigrationPlan) -> MigrationReport:
        """Simulate migration. NO mutations. Returns what WOULD happen."""
        report = MigrationReport(
            plan_name=plan.name,
            operation="dry_run",
            status=MigrationStatus.DRY_RUN,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            source_rows = self._fetch_source(plan)
            report.batch = MigrationBatch(
                batch_id=f"dry_{plan.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                plan_name=plan.name,
                started_at=report.started_at,
                total=len(source_rows),
            )
            for row in source_rows:
                identity_hash = plan.identity_fn(row)
                existing = _find_ledger_entry(identity_hash)
                record = MigrationRecord(
                    migration_id="",
                    batch_id=report.batch.batch_id,
                    source_table=plan.source.table_name,
                    source_pk=plan.source.pk_column,
                    source_pk_value=str(row.get(plan.source.pk_column, "")),
                    source_tenant_id=row.get(plan.source.tenant_column) if plan.source.tenant_column else None,
                    canonical_table=plan.target.table_name,
                    canonical_pk_value=identity_hash[:32],
                    target_tenant_id=plan.tenant_resolver(row) if plan.tenant_resolver else None,
                    identity_hash=identity_hash,
                    status="simulated",
                )
                if existing:
                    record.status = "would_skip"
                    report.batch.skipped += 1
                else:
                    record.status = "would_insert"
                    report.batch.success += 1
                report.records.append(record)

            report.status = MigrationStatus.DRY_RUN
            report.completed_at = datetime.now(timezone.utc).isoformat()
            return report

        except Exception as e:
            report.status = MigrationStatus.FAILED
            report.errors.append(str(e))
            report.completed_at = datetime.now(timezone.utc).isoformat()
            return report

    # ── Preflight ────────────────────────────────────────────────────

    def preflight(self, plan: MigrationPlan) -> MigrationReport:
        """Verify prerequisites before migration."""
        report = MigrationReport(
            plan_name=plan.name,
            operation="preflight",
            status=MigrationStatus.PREFLIGHT_PASS,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        checks = []

        # 1. Source table exists
        try:
            result = db.session.execute(
                db.text(f"SELECT 1 FROM {plan.source.table_name} LIMIT 1")
            ).scalar()
            checks.append(PreflightCheck(name="source_exists", passed=True, detail=f"Table {plan.source.table_name} is queryable"))
        except Exception as e:
            checks.append(PreflightCheck(name="source_exists", passed=False, detail=str(e)))

        # 2. Target table exists
        try:
            result = db.session.execute(
                db.text(f"SELECT 1 FROM {plan.target.table_name} LIMIT 1")
            ).scalar()
            checks.append(PreflightCheck(name="target_exists", passed=True, detail=f"Table {plan.target.table_name} is queryable"))
        except Exception as e:
            checks.append(PreflightCheck(name="target_exists", passed=False, detail=str(e)))

        # 3. Backup prerequisite
        # TODO: verify backup was taken

        report.preflight_checks = checks
        if not all(c.passed for c in checks):
            report.status = MigrationStatus.PREFLIGHT_FAIL

        report.completed_at = datetime.now(timezone.utc).isoformat()
        return report

    # ── Execute ──────────────────────────────────────────────────────

    def execute(self, plan: MigrationPlan) -> MigrationReport:
        """Execute migration. Transactional. Records to ledger."""
        report = MigrationReport(
            plan_name=plan.name,
            operation="execute",
            status=MigrationStatus.PENDING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Preflight check
        preflight = self.preflight(plan)
        if preflight.status == MigrationStatus.PREFLIGHT_FAIL:
            report.status = MigrationStatus.FAILED
            report.errors = [f"Preflight failed: {c.detail}" for c in preflight.preflight_checks if not c.passed]
            report.completed_at = datetime.now(timezone.utc).isoformat()
            return report

        try:
            source_rows = self._fetch_source(plan)
            batch = MigrationBatch(
                batch_id=f"mig_{plan.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                plan_name=plan.name,
                started_at=report.started_at,
                total=len(source_rows),
            )
            inserted_records: list[MigrationRecord] = []

            for row in source_rows:
                identity_hash = plan.identity_fn(row)
                existing = _find_ledger_entry(identity_hash)

                if existing and plan.on_conflict == "skip":
                    batch.skipped += 1
                    continue

                if existing and plan.on_conflict == "raise":
                    raise ValueError(f"Conflict: identity {identity_hash} already migrated")

                # Build canonical record fields
                target_data = {}
                for source_field, target_field in plan.target.field_map.items():
                    target_data[target_field] = row.get(source_field)
                target_data.update(plan.target.extra_fields)
                target_data[plan.target.identity_field] = identity_hash[:32]

                # Determine tenant
                tenant_id = None
                if plan.tenant_resolver:
                    tenant_id = plan.tenant_resolver(row)
                elif plan.target.tenant_column:
                    tenant_id = row.get(plan.source.tenant_column) if plan.source.tenant_column else None
                if plan.target.tenant_column:
                    target_data[plan.target.tenant_column] = tenant_id

                # Insert into canonical target
                insert_sql = self._build_upsert_sql(plan, target_data)
                db.session.execute(db.text(insert_sql), target_data)

                # Record to ledger (persisted in-memory; durable table optional)
                inserted_records.append(
                    MigrationRecord(
                        migration_id="",
                        batch_id=batch.batch_id,
                        source_table=plan.source.table_name,
                        source_pk=plan.source.pk_column,
                        source_pk_value=str(row.get(plan.source.pk_column, "")),
                        source_tenant_id=(
                            row.get(plan.source.tenant_column) if plan.source.tenant_column else None
                        ),
                        canonical_table=plan.target.table_name,
                        canonical_pk_value=target_data.get(
                            plan.target.pk_column, identity_hash[:32]
                        ),
                        target_tenant_id=tenant_id,
                        identity_hash=identity_hash,
                        status="committed",
                    )
                )
            db.session.commit()
            for rec in inserted_records:
                _log_to_ledger(rec)

            # Re-fetch to count actual target records
            result = db.session.execute(
                db.text(f"SELECT COUNT(*) FROM {plan.target.table_name}")
            ).scalar()
            batch.success = result or 0
            batch.status = "committed"
            report.batch = batch
            report.status = MigrationStatus.COMMITTED

        except Exception as e:
            db.session.rollback()
            report.status = MigrationStatus.FAILED
            report.errors.append(str(e))
            if report.batch:
                report.batch.status = "failed"
                report.batch.error = str(e)

        report.completed_at = datetime.now(timezone.utc).isoformat()
        return report

    # ── Reconcile ────────────────────────────────────────────────────

    def reconcile(self, plan: MigrationPlan) -> dict:
        """Verify all source records exist in the canonical target.

        Compares source vs destination counts for the migration's entity
        types and returns a real report dict::

            {
                "entity_type": <canonical target table>,
                "source_count": <rows in source query>,
                "destination_count": <rows in target table>,
                "missing": [identity hashes present in source but not target],
                "extra": [identity hashes present in target but not source],
                "status": "ok" | "error",
            }

        On failure the same shape is returned with ``status="error"`` and the
        exception message in ``error`` — reconcile never fabricates numbers.
        """
        try:
            source_rows = self._fetch_source(plan)
            # execute() persists identity_hash[:32] into the canonical target
            # (see execute() — canonical_pk_value). Compare the same width.
            src_identities = {plan.identity_fn(row)[:32] for row in source_rows}

            tgt_values = db.session.execute(
                db.text(
                    f"SELECT {plan.target.identity_field} FROM {plan.target.table_name}"
                )
            ).scalars().all()
            tgt_identities = {str(v) for v in tgt_values}

            missing = sorted(src_identities - tgt_identities)
            extra = sorted(tgt_identities - src_identities)
            report = {
                "entity_type": plan.target.table_name,
                "source_count": len(source_rows),
                "destination_count": len(tgt_identities),
                "missing": missing,
                "extra": extra,
                "status": "ok",
            }
            logger.info(
                "Reconcile %s: source=%d destination=%d missing=%d extra=%d",
                plan.name,
                report["source_count"],
                report["destination_count"],
                len(missing),
                len(extra),
            )
            return report
        except Exception as e:
            logger.warning("Reconcile %s failed: %s", plan.name, e)
            return {
                "entity_type": plan.target.table_name,
                "source_count": 0,
                "destination_count": 0,
                "missing": [],
                "extra": [],
                "status": "error",
                "error": str(e),
            }

    # ── Rollback ─────────────────────────────────────────────────────

    def rollback(self, plan: MigrationPlan) -> MigrationReport:
        """Rollback the last completed migration batch using the ledger.

        Migration records are looked up in a durable migration log/audit
        table when one exists (``data_migration_ledger``, ``migration_ledger``,
        ``data_migration_log``, ``migration_log``, ``migration_audit``),
        otherwise in the in-memory ``MIGRATION_LEDGER``. The target rows of
        the most recent committed batch are deleted and the records are
        marked ``rolled_back``.

        If no rollback source exists yet, the report carries an honest
        message instead of raising ``NotImplementedError``.
        """
        report = MigrationReport(
            plan_name=plan.name,
            operation="rollback",
            status=MigrationStatus.PENDING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            records, source = self._collect_committed_records(plan)

            if not records:
                report.status = MigrationStatus.FAILED
                report.errors.append(
                    "No rollback mechanism exists yet: no durable migration "
                    "log/audit table is present and the in-memory migration "
                    f"ledger holds no committed records for plan '{plan.name}' "
                    f"(source {plan.source.table_name} → target "
                    f"{plan.target.table_name}). Persist a migration ledger "
                    "(e.g. a 'migration_ledger' table populated by execute()) "
                    "to enable rollback."
                )
                report.completed_at = datetime.now(timezone.utc).isoformat()
                return report

            batch_id = records[0].batch_id
            deleted = 0
            for rec in records:
                result = db.session.execute(
                    db.text(
                        f"DELETE FROM {plan.target.table_name} "
                        f"WHERE {plan.target.pk_column} = :pk"
                    ),
                    {"pk": rec.canonical_pk_value},
                )
                deleted += result.rowcount or 0
            db.session.commit()

            now = datetime.now(timezone.utc).isoformat()
            for rec in records:
                rec.status = "rolled_back"
                rec.rolled_back_at = now

            report.records = records
            report.batch = MigrationBatch(
                batch_id=batch_id,
                plan_name=plan.name,
                started_at=records[0].created_at,
                completed_at=now,
                status="rolled_back",
                total=len(records),
                success=deleted,
            )
            report.status = MigrationStatus.ROLLED_BACK
            logger.info(
                "Rolled back batch %s (%s): deleted %d rows from %s",
                batch_id, source, deleted, plan.target.table_name,
            )
        except Exception as e:
            db.session.rollback()
            report.status = MigrationStatus.FAILED
            report.errors.append(str(e))

        report.completed_at = datetime.now(timezone.utc).isoformat()
        return report

    # ── Rollback support helpers ─────────────────────────────────────

    def _find_migration_log_table(self) -> Optional[str]:
        """Return the name of a durable migration log/audit table if one exists."""
        try:
            from sqlalchemy import inspect as sa_inspect
            tables = set(sa_inspect(db.engine).get_table_names())
        except Exception:
            return None
        for candidate in (
            "data_migration_ledger",
            "migration_ledger",
            "data_migration_log",
            "migration_log",
            "migration_audit",
        ):
            if candidate in tables:
                return candidate
        return None

    def _collect_committed_records(
        self, plan: MigrationPlan
    ) -> tuple[list[MigrationRecord], str]:
        """Collect committed migration records for *plan* (last batch).

        Prefers a durable migration log/audit table; falls back to the
        in-memory ``MIGRATION_LEDGER``. Returns ``(records, source)`` where
        *source* describes where the records came from.
        """
        log_table = self._find_migration_log_table()
        if log_table:
            try:
                rows = db.session.execute(
                    db.text(
                        f"SELECT * FROM {log_table} "
                        f"WHERE status = 'committed' "
                        f"AND source_table = :st AND canonical_table = :ct"
                    ),
                    {"st": plan.source.table_name, "ct": plan.target.table_name},
                ).mappings().all()
                if rows:
                    records = [
                        MigrationRecord(
                            migration_id=str(r.get("migration_id", "") or ""),
                            batch_id=str(r.get("batch_id", "") or ""),
                            source_table=str(r.get("source_table", "") or ""),
                            source_pk=str(r.get("source_pk", "") or ""),
                            source_pk_value=str(r.get("source_pk_value", "") or ""),
                            source_tenant_id=r.get("source_tenant_id"),
                            canonical_table=str(r.get("canonical_table", "") or ""),
                            canonical_pk_value=str(r.get("canonical_pk_value", "") or ""),
                            target_tenant_id=r.get("target_tenant_id"),
                            identity_hash=str(r.get("identity_hash", "") or ""),
                            status="committed",
                        )
                        for r in rows
                    ]
                    records.sort(key=lambda rec: rec.created_at)
                    batch_id = records[-1].batch_id
                    return [r for r in records if r.batch_id == batch_id], (
                        f"migration log table {log_table}"
                    )
            except Exception as exc:
                logger.warning(
                    "Durable migration log read failed (%s) — using in-memory ledger",
                    exc,
                )

        committed = [
            r
            for r in MIGRATION_LEDGER
            if r.status == "committed"
            and r.source_table == plan.source.table_name
            and r.canonical_table == plan.target.table_name
        ]
        if committed:
            committed.sort(key=lambda rec: rec.created_at)
            batch_id = committed[-1].batch_id
            return [r for r in committed if r.batch_id == batch_id], (
                "in-memory migration ledger"
            )
        return [], "no migration log/audit table"

    # ── Helpers ──────────────────────────────────────────────────────

    def _fetch_source(self, plan: MigrationPlan) -> list[dict]:
        """Fetch source data for migration."""
        result = db.session.execute(db.text(plan.source.query))
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def _build_upsert_sql(self, plan: MigrationPlan, data: dict) -> str:
        """Build PostgreSQL upsert (INSERT ... ON CONFLICT) SQL."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        updates = ", ".join(f"{k} = EXCLUDED.{k}" for k in data.keys())
        # Note: PK must be identity_field = canonical_pk_value
        return (
            f"INSERT INTO {plan.target.table_name} ({columns}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT ({plan.target.pk_column}) DO UPDATE SET {updates}"
        )

    def _backup_prerequisite(self, plan: MigrationPlan) -> bool:
        """Verify a database backup exists before migration."""
        # TODO: implement backup check
        return True


# ═══════════════════════════════════════════════════════════════════════
# Identity functions
# ═══════════════════════════════════════════════════════════════════════


def deterministic_hash(row: dict, fields: Optional[list[str]] = None) -> str:
    """Generate a deterministic hash from source record fields.

    Same source data → same hash every time. Idempotency guarantee.
    """
    if fields:
        relevant = {k: row.get(k) for k in fields}
    else:
        relevant = {k: v for k, v in row.items() if k not in ("updated_at", "created_at", "version")}
    raw = json.dumps(relevant, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def deterministic_uuid(row: dict, fields: Optional[list[str]] = None) -> str:
    """UUID v5 (namespace-based, deterministic) from source fields."""
    import uuid as _uuid
    ns = _uuid.NAMESPACE_DNS
    if fields:
        raw = "|".join(str(row.get(k, "")) for k in fields)
    else:
        raw = json.dumps(row, sort_keys=True, default=str)
    return str(_uuid.uuid5(ns, raw))