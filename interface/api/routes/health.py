"""Health check route handler."""

from fastapi import APIRouter

from core.database import check_schema_health
from interface.api.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["System"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with database connectivity and schema verification."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    status = "healthy"
    
    # Check database if configured
    if database_url:
        try:
            schema_health = await check_schema_health()
            if schema_health.get("status") != "healthy":
                status = "degraded"
        except Exception:
            status = "degraded"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
    )

