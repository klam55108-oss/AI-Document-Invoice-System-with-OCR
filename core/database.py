"""Async database connection and session management."""

import asyncio
from typing import Any, AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from core.logging import get_logger

logger = get_logger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()

# Global engine and session factory
_engine = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str, max_retries: int = 3, retry_delay: float = 1.0) -> None:
    """Initialize database connection pool with retry logic.
    
    Args:
        database_url: Database connection URL
        max_retries: Maximum number of connection retry attempts
        retry_delay: Delay between retry attempts in seconds
    """
    global _engine, _async_session_factory

    if _engine is not None:
        logger.warning("Database already initialized")
        return

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            _engine = create_async_engine(
                database_url,
                echo=False,  # Set to True for SQL query logging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
            )

            _async_session_factory = async_sessionmaker(
                _engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            # Test connection
            async with _async_session_factory() as test_session:
                await test_session.execute(text("SELECT 1"))
            
            logger.info("Database connection pool initialized", attempt=attempt)
            return
        except Exception as e:
            last_error = e
            logger.warning(
                "Database connection attempt failed",
                attempt=attempt,
                max_retries=max_retries,
                error=str(e),
            )
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * attempt)  # Exponential backoff
    
    # If all retries failed, raise the last error
    logger.error("Failed to initialize database after all retries", error=str(last_error))
    raise RuntimeError(f"Failed to initialize database after {max_retries} attempts: {last_error}") from last_error


async def close_db() -> None:
    """Close database connection pool."""
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database connection pool closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_engine():
    """Get the async engine (for Alembic migrations)."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory for manual session management."""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_factory


async def check_schema_health() -> dict[str, Any]:
    """Check database schema health by verifying key tables and columns exist.
    
    Returns:
        Dictionary with health check results:
        - status: "healthy" or "unhealthy"
        - tables_checked: List of tables that were checked
        - missing_tables: List of expected tables that are missing
        - schema_version: Current Alembic revision if available
        - errors: List of error messages
    """
    if _engine is None:
        return {
            "status": "unhealthy",
            "error": "Database not initialized",
            "tables_checked": [],
            "missing_tables": [],
        }
    
    result: dict[str, Any] = {
        "status": "healthy",
        "tables_checked": [],
        "missing_tables": [],
        "errors": [],
    }
    
    # Expected tables from data model
    expected_tables = [
        "invoices",
        "extracted_data",
        "validation_results",
        "processing_jobs",
        "ocr_results",
        "ocr_comparisons",
    ]
    expected_columns = {
        "invoices": ["id", "storage_path", "file_name", "file_hash", "processing_status", "created_at"],
        "extracted_data": ["id", "invoice_id", "vendor_name", "total_amount"],
        "validation_results": ["id", "invoice_id", "rule_name", "status"],
        "processing_jobs": ["id", "invoice_id", "job_type", "status"],
        "ocr_results": ["id", "input_id", "provider_id", "status", "created_at"],
        "ocr_comparisons": ["id", "input_id", "provider_a_result_id", "provider_b_result_id"],
    }
    
    try:
        async with _async_session_factory() as session:
            # Check if tables exist using SQL query (works with async engine)
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables_result = await session.execute(tables_query)
            existing_tables = [row[0] for row in tables_result.fetchall()]
            
            for table in expected_tables:
                if table in existing_tables:
                    result["tables_checked"].append(table)
                    # Check key columns using SQL query
                    columns_query = text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = :table_name
                    """)
                    columns_result = await session.execute(columns_query, {"table_name": table})
                    columns = [row[0] for row in columns_result.fetchall()]
                    missing_cols = [col for col in expected_columns.get(table, []) if col not in columns]
                    if missing_cols:
                        result["errors"].append(f"Table {table} missing columns: {', '.join(missing_cols)}")
                        result["status"] = "unhealthy"
                else:
                    result["missing_tables"].append(table)
                    result["status"] = "unhealthy"
            
            # Check Alembic version
            try:
                version_result = await session.execute(text("SELECT version_num FROM alembic_version"))
                version_row = version_result.first()
                if version_row:
                    result["schema_version"] = version_row[0]
            except Exception as e:
                logger.warning("Could not retrieve Alembic version", error=str(e))
                result["errors"].append(f"Could not retrieve schema version: {str(e)}")
    
    except Exception as e:
        logger.error("Schema health check failed", error=str(e))
        result["status"] = "unhealthy"
        result["errors"].append(f"Health check failed: {str(e)}")
    
    return result

