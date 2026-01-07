"""PgQueuer initialization and context management for version 0.25.3+."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from pgqueuer import PgQueuer, Queries, AsyncpgDriver
from core.logging import get_logger

logger = get_logger(__name__)

# Global instances
_pgq: PgQueuer | None = None
_queries: Queries | None = None
_worker_conn: asyncpg.Connection | None = None
_enqueuer_conn: asyncpg.Connection | None = None

async def get_pgq() -> PgQueuer:
    """Get the global PgQueuer instance (for worker)."""
    global _pgq, _worker_conn
    if _pgq is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not set")
        
        # pgqueuer needs a standard postgresql connection
        _worker_conn = await asyncpg.connect(database_url.replace("postgresql+asyncpg://", "postgresql://"))
        _pgq = PgQueuer.from_asyncpg_connection(_worker_conn)
    
    return _pgq

async def get_queries() -> Queries:
    """Get the global Queries instance (for enqueueing)."""
    global _queries, _enqueuer_conn
    if _queries is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not set")
            
        _enqueuer_conn = await asyncpg.connect(database_url.replace("postgresql+asyncpg://", "postgresql://"))
        _queries = Queries(AsyncpgDriver(_enqueuer_conn))
            
    return _queries

async def init_queue() -> PgQueuer:
    """Initialize the queue for use in the application."""
    return await get_pgq()

async def close_queue() -> None:
    """Close the global queue connections."""
    global _worker_conn, _enqueuer_conn, _pgq, _queries
    if _worker_conn is not None:
        await _worker_conn.close()
        _worker_conn = None
        _pgq = None
    if _enqueuer_conn is not None:
        await _enqueuer_conn.close()
        _enqueuer_conn = None
        _queries = None
    logger.info("Job queue connections closed")
