"""
Alembic environment configuration.

Supports both:
  - Offline mode (--sql flag): generates SQL scripts
  - Online mode (default): connects directly to the database

Uses the SYNC_DATABASE_URL (psycopg2) setting because Alembic's standard
runner is synchronous. For async migrations, see the --async flag pattern.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Ensure the project root is on sys.path ────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Load all models so autogenerate can detect them ──────────────────────────
# This import must happen BEFORE `target_metadata` is read.
from app.models import *  # noqa: F401, F403 – side-effect import
from app.config.database import Base
from app.config.settings import settings

# Alembic Config object
config = context.config

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object used by autogenerate
target_metadata = Base.metadata

# Override sqlalchemy.url from settings so .env controls the connection
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)


# ── Offline migration ─────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configures the context with just a URL (no Engine).
    Useful for generating SQL scripts without a live DB.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online migration ──────────────────────────────────────────────────────────

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Creates an Engine from config and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # Include schemas if using Supabase with non-public schemas
            include_schemas=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
