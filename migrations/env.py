from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app import db
from app.models import Lead, Payment, Supplier, Invoice, ItineraryRef
target_metadata = db.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # Read DATABASE_URL from environment, fall back to alembic.ini
    db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    config_section = config.get_section(config.config_ini_section)
    config_section["sqlalchemy.url"] = db_url
    connectable = engine_from_config(config_section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
