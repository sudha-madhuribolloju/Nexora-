"""
alembic/env.py
──────────────
Alembic async migration environment.

IMPORTANT: Every SQLAlchemy model file MUST be imported below (inside
`_import_all_models`) so that `Base.metadata` contains the complete schema
when `alembic revision --autogenerate` or `alembic check` is run.

Add new model imports here as each migration module is created.
"""

import asyncio
import logging
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.database.base import Base

log = logging.getLogger("alembic.env")

# ── Alembic config object ──────────────────────────────────────────────────────
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ── Model imports — keep this block up to date ────────────────────────────────

def _import_all_models() -> None:
    """
    Import every ORM model so Base.metadata is fully populated.
    Alembic autogenerate compares Base.metadata against the live DB schema.
    Failure to import a model here means its table is invisible to Alembic.
    """
    # ── Core / Auth ────────────────────────────────────────────────────────
    import app.models.user          # noqa: F401

    # ── Migration 001 — RBAC ───────────────────────────────────────────────
    import app.models.roles         # noqa: F401

    # ── Migration 002 — Schools ──────────────────────────────────────
    import app.models.school      # noqa: F401

    # ── Migration 003 — Academics ────────────────────────────────────
    import app.models.academic    # noqa: F401

    # —— Migration 005 — People ————————————————————————————————————
    import app.models.people      # noqa: F401

    # —— Migration 006 — Courses, Sessions, Attendance, Assignments, Quizzes, Notifications, Documents, KB
    import app.models.course        # noqa: F401
    import app.models.subject       # noqa: F401  (CourseSubject)
    import app.models.session       # noqa: F401  (ClassSession)
    import app.models.attendance    # noqa: F401
    import app.models.assignment    # noqa: F401
    import app.models.quiz          # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.document      # noqa: F401
    import app.models.knowledge_base  # noqa: F401

    # —— Migration 007 — AI / Knowledge Chunks (pgvector) ————————————
    # import app.models.ai_conversation  # noqa: F401
    # import app.models.knowledge        # noqa: F401

    # —— Migration 008 — Audit Log (future) ——————————————————————————
    # import app.models.audit_log  # noqa: F401


_import_all_models()
target_metadata = Base.metadata


# ── Offline migrations ─────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations ──────────────────────────────────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# ── Entry point ────────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())