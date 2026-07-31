"""SHUNYA — Persistence Layer.

Database session management, connection pooling, and migration runner.
Backed by SQLAlchemy. Provides a session factory for engine use.

Architectural authority: INFR-003 (SHUNYA_IMPLEMENTATION_PROGRAM.md)
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class Database:
    """Database connection manager.

    Provides:
      - Engine creation with connection pooling
      - Session factory for ORM sessions
      - Migration runner (Alembic integration)
      - Health check
    """

    def __init__(
        self,
        database_url: str = "sqlite:///:memory:",
        pool_size: int = 5,
        pool_timeout: int = 30,
        echo: bool = False,
        migration_dir: Optional[str] = None,
    ) -> None:
        self._database_url = database_url
        self._pool_size = pool_size
        self._pool_timeout = pool_timeout
        self._echo = echo
        self._migration_dir = migration_dir

        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    # ---- Engine -------------------------------------------------------------

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            kwargs: Dict[str, Any] = {
                "echo": self._echo,
                "pool_pre_ping": True,  # verify connections before use
            }
            if "sqlite" not in self._database_url:
                kwargs["pool_size"] = self._pool_size
                kwargs["pool_timeout"] = self._pool_timeout
                kwargs["max_overflow"] = 10
            # Handle SQLite pragmas for WAL mode
            if "sqlite" in self._database_url:
                # Ensure directory for file-based SQLite
                if self._database_url != "sqlite:///:memory:":
                    db_path = self._database_url.replace("sqlite:///", "")
                    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

                @event.listens_for(Engine, "connect")
                def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            self._engine = create_engine(self._database_url, **kwargs)
        return self._engine

    # ---- Sessions -----------------------------------------------------------

    @property
    def session_factory(self) -> sessionmaker:
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def create_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager that provides a session and commits/rolls back."""
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---- Health -------------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity. Returns status dict."""
        result: Dict[str, Any] = {"status": "unknown"}
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            result["status"] = "connected"
            result["database_url"] = self._database_url[:30] + "..."
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        return result

    # ---- Migration ----------------------------------------------------------

    def run_migrations(self, migration_dir: Optional[str] = None) -> None:
        """Run Alembic migrations if available.

        Args:
            migration_dir: Path to Alembic migrations directory.
                           Falls back to self._migration_dir if not provided.
        """
        dir_path = migration_dir or self._migration_dir
        if not dir_path:
            return
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command

            alembic_cfg = AlembicConfig()
            alembic_cfg.set_main_option("script_location", dir_path)
            alembic_cfg.set_main_option("sqlalchemy.url", self._database_url)
            command.upgrade(alembic_cfg, "head")
        except ImportError:
            pass  # Alembic not installed — skip migrations
        except Exception:
            raise

    def dispose(self) -> None:
        """Dispose of the engine and all connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# ---- Module-level convenience -----------------------------------------------

_db: Optional[Database] = None


def get_database(
    database_url: Optional[str] = None,
    pool_size: Optional[int] = None,
    pool_timeout: Optional[int] = None,
    echo: Optional[bool] = None,
    migration_dir: Optional[str] = None,
) -> Database:
    """Return the application-wide Database instance (lazily created)."""
    global _db
    if _db is None:
        from app.shunya.config import get_config

        cfg = get_config()
        persistence_cfg = cfg.get_section("persistence")
        _db = Database(
            database_url=database_url or persistence_cfg.get("database_url", "sqlite:///:memory:"),
            pool_size=pool_size or persistence_cfg.get("pool_size", 5),
            pool_timeout=pool_timeout or persistence_cfg.get("pool_timeout_s", 30),
            echo=echo or persistence_cfg.get("echo", False),
            migration_dir=migration_dir or persistence_cfg.get("migration_dir"),
        )
    return _db


def reset_database() -> None:
    """Reset the global database instance. Useful for testing."""
    global _db
    if _db:
        _db.dispose()
    _db = None