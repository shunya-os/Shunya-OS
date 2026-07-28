"""Tests for INFR-003: Persistence Layer."""

import pytest
from sqlalchemy import Column, Integer, String, text
from app.shunya.infrastructure.persistence import Database, get_database, reset_database


class TestDatabase:
    def test_create_engine_sqlite(self) -> None:
        db = Database("sqlite:///:memory:")
        engine = db.engine
        assert engine is not None
        # Verify connection works
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_session_context_manager(self) -> None:
        db = Database("sqlite:///:memory:")
        with db.session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_session_rollback_on_error(self) -> None:
        db = Database("sqlite:///:memory:")
        # Set up a table
        with db.session() as session:
            session.execute(text("CREATE TABLE test_t (id INTEGER PRIMARY KEY, val TEXT)"))
            session.execute(text("INSERT INTO test_t (id, val) VALUES (1, 'hello')"))
        # Rollback on error
        with pytest.raises(Exception):
            with db.session() as session:
                session.execute(text("INSERT INTO test_t (id, val) VALUES (2, 'world')"))
                raise RuntimeError("force rollback")
        # Verify that the insert was rolled back
        with db.session() as session:
            result = session.execute(text("SELECT COUNT(*) FROM test_t"))
            assert result.scalar() == 1

    def test_health_check_connected(self) -> None:
        db = Database("sqlite:///:memory:")
        health = db.health_check()
        assert health["status"] == "connected"

    def test_health_check_result_structure(self) -> None:
        db = Database("sqlite:///:memory:")
        health = db.health_check()
        assert "status" in health
        assert "database_url" in health

    def test_dispose(self) -> None:
        db = Database("sqlite:///:memory:")
        engine_before = db.engine
        db.dispose()
        assert db.engine is not engine_before

    def test_session_factory(self) -> None:
        db = Database("sqlite:///:memory:")
        factory = db.session_factory
        session = factory()
        try:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        finally:
            session.close()

    def test_none_default_pool_params_for_sqlite(self) -> None:
        # SQLite shouldn't have pool settings
        db = Database("sqlite:///:memory:")
        engine = db.engine
        # Should not error — SQLite path avoids pool configuration
        assert engine is not None

    def test_module_level_get_database(self) -> None:
        reset_database()
        # Reset config too so get_database creates fresh
        from app.shunya.config import reset_config
        reset_config()
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2

    def test_session_commit(self) -> None:
        db = Database("sqlite:///:memory:")
        with db.session() as session:
            session.execute(text("CREATE TABLE test_commit (id INTEGER PRIMARY KEY, val TEXT)"))
            session.execute(text("INSERT INTO test_commit (id, val) VALUES (1, 'committed')"))
        # Verify the data persists across sessions
        with db.session() as session:
            result = session.execute(text("SELECT val FROM test_commit WHERE id = 1"))
            assert result.scalar() == "committed"