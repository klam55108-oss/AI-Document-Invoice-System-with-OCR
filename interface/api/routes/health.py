"""Health check route handler."""

from fastapi import APIRouter

from interface.api.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["System"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
    )

