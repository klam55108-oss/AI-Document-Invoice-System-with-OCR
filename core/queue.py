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
_conn: asyncpg.Connection | None = None

async def get_pgq() -> PgQueuer:
    """Get the global PgQueuer instance (for worker)."""
    global _pgq, _conn
    if _pgq is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not set")
        
        # pgqueuer needs a standard postgresql connection
        _conn = await asyncpg.connect(database_url.replace("postgresql+asyncpg://", "postgresql://"))
        _pgq = PgQueuer.from_asyncpg_connection(_conn)
    
    return _pgq

async def get_queries() -> Queries:
    """Get the global Queries instance (for enqueueing)."""
    global _queries, _conn
    if _queries is None:
        if _conn is None:
            await get_pgq()
        
        # If we have a connection now, create the queries instance
        if _conn is not None:
            _queries = Queries(AsyncpgDriver(_conn))
        else:
            raise RuntimeError("Failed to establish database connection")
            
    return _queries

async def init_queue() -> PgQueuer:
    """Initialize the queue for use in the application."""
    return await get_pgq()

async def close_queue() -> None:
    """Close the global queue connection."""
    global _conn, _pgq, _queries
    if _conn is not None:
        await _conn.close()
        _conn = None
        _pgq = None
        _queries = None
        logger.info("Job queue connection closed")
