"""
app/database/session.py
────────────────────────
Database session factory and application startup logic.

Changes from original:
  • init_database() no longer calls create_all(). Schema is managed exclusively
    by Alembic migrations.
  • Each startup operation runs in its OWN engine.begin() block so that a
    failed pgvector CREATE EXTENSION (e.g. extension not installed at OS level)
    does NOT abort the transaction used for the HNSW index statement. Previously
    both ops shared one transaction; the first exception put it into an aborted
    state and the second op silently failed.
"""

import logging

from sqlalchemy import text

from app.database.database import engine, SessionLocal, get_db  # noqa: F401

logger = logging.getLogger("app.database.session")


async def init_database() -> None:
    """
    Idempotent startup hook. Each step runs in an independent transaction so
    one failure does not cascade to subsequent steps.
    """
    # ── Step 1: pgvector extension ─────────────────────────────────────────────
    # Requires: apt install postgresql-16-pgvector (or equivalent for your PG version)
    # on the server running PostgreSQL, then a superuser must run CREATE EXTENSION.
    # If the extension is not installed at the OS level, this will warn + skip.
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("pgvector extension enabled or already present.")
    except Exception as exc:
        logger.warning(
            "pgvector extension not available — AI embedding features will be "
            "disabled until the extension is installed. Error: %s", exc,
        )

    # ── Step 2: HNSW index on knowledge_chunks ─────────────────────────────────
    # knowledge_chunks table is created by Migration 007.
    # This step is silently skipped until that migration runs.
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding "
                    "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);"
                )
            )
            logger.info("HNSW index on knowledge_chunks.embedding verified.")
    except Exception as exc:
        logger.debug(
            "HNSW index skipped (knowledge_chunks not yet created): %s", exc
        )

    logger.info("Database startup hook complete.")