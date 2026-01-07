"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import close_db, init_db
from core.logging import configure_logging, get_logger
from core.queue import init_queue
from core.jobs import register_handlers
from interface.api.routes import analytics, chatbot, health, invoices, uploads
from brain.chatbot.session_manager import session_manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "json")
    configure_logging(log_level=log_level, log_format=log_format)

    # Initialize database
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        await init_db(database_url)
        # Initialize queue
        queue = await init_queue()
        await register_handlers()
        # Start the queue listener in the background
        import asyncio
        app.state.queue_task = asyncio.create_task(queue.run())
        
        # Start session cleanup background task
        async def cleanup_sessions_periodically():
            """Periodically clean up expired chatbot sessions."""
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    removed = session_manager.cleanup_expired()
                    if removed > 0:
                        logger.info("Cleaned up expired chatbot sessions", count=removed)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Error in session cleanup task", error=str(e))
        
        app.state.session_cleanup_task = asyncio.create_task(cleanup_sessions_periodically())
        logger.info("Application started and job queue listener running")
    else:
        logger.warning("DATABASE_URL not set, database not initialized")

    yield

    # Shutdown
    if hasattr(app.state, "queue_task"):
        app.state.queue_task.cancel()
        try:
            await app.state.queue_task
        except asyncio.CancelledError:
            pass
    
    if hasattr(app.state, "session_cleanup_task"):
        app.state.session_cleanup_task.cancel()
        try:
            await app.state.session_cleanup_task
        except asyncio.CancelledError:
            pass
    
    await close_db()
    logger.info("Application shutdown")


# Create FastAPI app
app = FastAPI(
    title="E-Invoice Processing API",
    version="1.0.0",
    description="API for processing and querying invoice documents",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(invoices.router)
app.include_router(analytics.router)
app.include_router(uploads.router)
app.include_router(chatbot.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AgenticAG E-Invoice Processing API",
        "version": "1.0.0",
        "docs": "/docs",
    }


def main():
    """Main entry point for running the API server."""
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

