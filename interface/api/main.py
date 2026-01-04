"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import close_db, init_db
from core.logging import configure_logging, get_logger
from interface.api.routes import health, invoices

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
        logger.info("Application started")
    else:
        logger.warning("DATABASE_URL not set, database not initialized")

    yield

    # Shutdown
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "E-Invoice Processing API",
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

