"""
Database engine, async session factory, and initialization.

Uses aiosqlite for async SQLite access throughout FastAPI.
Registers updated_at triggers for all TimestampMixin tables on creation.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import event, inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

try:
    # Try package imports first
    from agileai.models import Base, TimestampMixin
except ImportError:
    # Fallback to root imports
    from __init__ import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = Path(os.getenv("AGILEAI_DB_PATH", "./agileai.db"))
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("AGILEAI_SQL_ECHO", "")),
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with get_session() as session:
        yield session


# ---------------------------------------------------------------------------
# SQLite pragmas — run on every new connection
# ---------------------------------------------------------------------------
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    # Write-Ahead Logging: allows concurrent reads during writes
    cursor.execute("PRAGMA foreign_keys=ON")
    # Enforce FK constraints (disabled by default in SQLite)
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Balanced durability/performance
    cursor.execute("PRAGMA cache_size=-64000")
    # 64MB page cache
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


# ---------------------------------------------------------------------------
# Updated_at triggers — registered after each table is created
# ---------------------------------------------------------------------------
def _register_updated_at_trigger(target, connection, **kw):
    """
    Auto-register an AFTER UPDATE trigger for updated_at
    on any table whose model uses TimestampMixin.
    """
    table_name = target.name
    connection.execute(text(f"""
        CREATE TRIGGER IF NOT EXISTS trg_{table_name}_updated_at
        AFTER UPDATE ON {table_name}
        FOR EACH ROW
        BEGIN
            UPDATE {table_name}
            SET updated_at = CURRENT_TIMESTAMP
            WHERE rowid = NEW.rowid;
        END;
    """))


def _attach_triggers():
    """Attach updated_at trigger to all TimestampMixin tables."""
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if issubclass(cls, TimestampMixin):
            table = cls.__table__
            if not any(
                getattr(l, "_agileai_trigger_attached", False)
                for l in table._listeners.get("after_create", [])
            ):
                listener = lambda t, conn, **kw: _register_updated_at_trigger(t, conn, **kw)
                listener._agileai_trigger_attached = True
                event.listen(table, "after_create", listener)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
async def init_db(seed: bool = True) -> None:
    """
    Create all tables, register triggers, and optionally seed initial data.
    Safe to call multiple times — uses CREATE IF NOT EXISTS.
    """
    _attach_triggers()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if seed:
        await _seed_initial_data()


async def _seed_initial_data() -> None:
    """Seed built-in roles, permissions, and default compression rules."""
    from agileai.models.rbac import BUILT_IN_ROLES, Role
    from agileai.services.seed import seed_roles_and_permissions, seed_compression_rules

    async with AsyncSessionLocal() as session:
        await seed_roles_and_permissions(session)
        await seed_compression_rules(session)
        await session.commit()


async def drop_db() -> None:
    """Drop all tables. Use only in tests or development reset."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
