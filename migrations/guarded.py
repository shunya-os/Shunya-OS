"""Guarded DDL facade for the SHUNYA Alembic chain (R6B-2.5).

WHY THIS EXISTS
---------------
SHUNYA has two schema authorities:

  1. the SQLAlchemy model metadata, materialised at application boot by
     ``db.create_all()`` (app/__init__.py), and
  2. the Alembic revision chain in ``migrations/versions/``.

The revision chain was authored as a *delta* against a pre-existing legacy
database, so it could not run from a genuinely fresh database. Reproduced on
the R6B-2.5 disposable PostgreSQL cluster:

  * alembic-first  -> ``0006`` runs ``ALTER TABLE commitments ADD COLUMN ...``
    and dies with ``UndefinedTable: relation "commitments" does not exist``
    (no revision in the chain creates that table).
  * boot-first     -> ``0001`` runs ``CREATE TABLE tenants`` and dies with
    ``DuplicateTable: relation "tenants" already exists`` (``db.create_all()``
    already made it from the model).

Neither order converged, so certification previously had to be faked with a
manual ``ALTER TABLE`` plus ``alembic stamp head``. This module removes that
need.

WHAT IT DOES
------------
``guarded_op(op)`` returns a facade over Alembic's ``Operations`` proxy that
performs each DDL step only when it is genuinely required, decided by an
explicit ``information_schema`` / ``pg_catalog`` lookup — never by swallowing
exceptions, so a real error still raises.

Convergence rule: a *missing* table is not an error. On a fresh database any
table absent from the chain is materialised by the canonical boot path from the
model definitions, which already carries every column the model declares. Each
revision therefore converges to the same schema from any starting point and the
chain needs no manual ``ALTER TABLE``, ``CREATE INDEX`` or ``alembic stamp``.

Un-guarded operations (``execute``, ``get_bind``, ``f``, ...) pass straight
through to the real proxy.
"""
from __future__ import annotations

from alembic import op as _default_op


class GuardedOps:
    """Existence-aware facade over Alembic's ``op`` proxy."""

    def __init__(self, op):
        self._op = op

    # -- existence probes --------------------------------------------------
    def _scalar(self, sql, **params):
        from sqlalchemy import text
        return self._op.get_bind().execute(text(sql), params).scalar()

    def has_table(self, table_name):
        return self._scalar(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :t AND table_schema = ANY(current_schemas(false))",
            t=table_name,
        ) is not None

    def has_column(self, table_name, column_name):
        if not self.has_table(table_name):
            return False
        return self._scalar(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c "
            "AND table_schema = ANY(current_schemas(false))",
            t=table_name, c=column_name,
        ) is not None

    def has_index(self, index_name):
        return self._scalar(
            "SELECT 1 FROM pg_indexes WHERE indexname = :n "
            "AND schemaname = ANY(current_schemas(false))",
            n=index_name,
        ) is not None

    def has_constraint(self, constraint_name, table_name=None):
        if table_name is not None:
            return self._scalar(
                "SELECT 1 FROM pg_constraint WHERE conname = :n AND conrelid = "
                "to_regclass(:t)::oid",
                n=constraint_name, t=table_name,
            ) is not None
        return self._scalar(
            "SELECT 1 FROM pg_constraint WHERE conname = :n", n=constraint_name
        ) is not None

    # -- guarded DDL -------------------------------------------------------
    def create_table(self, table_name, *args, **kwargs):
        if self.has_table(table_name):
            return None
        return self._op.create_table(table_name, *args, **kwargs)

    def create_index(self, index_name, table_name, columns, **kwargs):
        if self.has_index(index_name):
            return None
        if not self.has_table(table_name):
            return None
        return self._op.create_index(index_name, table_name, columns, **kwargs)

    def add_column(self, table_name, column, **kwargs):
        column_name = getattr(column, "name", None)
        if not self.has_table(table_name):
            return None
        if column_name and self.has_column(table_name, column_name):
            return None
        return self._op.add_column(table_name, column, **kwargs)

    def alter_column(self, table_name, column_name, **kwargs):
        if not self.has_column(table_name, column_name):
            return None
        return self._op.alter_column(table_name, column_name, **kwargs)

    def create_unique_constraint(self, constraint_name, table_name, columns, **kwargs):
        if self.has_constraint(constraint_name, table_name):
            return None
        if not self.has_table(table_name):
            return None
        return self._op.create_unique_constraint(
            constraint_name, table_name, columns, **kwargs)

    def create_foreign_key(self, constraint_name, source_table, referent_table,
                           local_cols, remote_cols, **kwargs):
        if self.has_constraint(constraint_name, source_table):
            return None
        if not (self.has_table(source_table) and self.has_table(referent_table)):
            return None
        return self._op.create_foreign_key(
            constraint_name, source_table, referent_table,
            local_cols, remote_cols, **kwargs)

    def drop_table(self, table_name, **kwargs):
        if not self.has_table(table_name):
            return None
        return self._op.drop_table(table_name, **kwargs)

    def drop_column(self, table_name, column_name, **kwargs):
        if not self.has_column(table_name, column_name):
            return None
        return self._op.drop_column(table_name, column_name, **kwargs)

    def drop_index(self, index_name, **kwargs):
        if not self.has_index(index_name):
            return None
        return self._op.drop_index(index_name, **kwargs)

    def drop_constraint(self, constraint_name, table_name=None, **kwargs):
        if not self.has_constraint(constraint_name, table_name):
            return None
        return self._op.drop_constraint(constraint_name, table_name, **kwargs)

    # -- everything else passes through (execute, get_bind, f, ...) --------
    def __getattr__(self, name):
        return getattr(self._op, name)


def guarded_op(op=None):
    """Wrap an Alembic ``Operations`` proxy with existence-aware guards."""
    return GuardedOps(op if op is not None else _default_op)
