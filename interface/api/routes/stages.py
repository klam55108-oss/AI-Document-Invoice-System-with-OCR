"""Processing stage routes."""

from fastapi import APIRouter

from core.module_registry import list_stages
from interface.api.schemas import StageInfo, StageListResponse

router = APIRouter(prefix="/api/v1/stages", tags=["stages"])


@router.get("", response_model=StageListResponse)
async def list_processing_stages() -> StageListResponse:
    """List processing stages."""
    stages = [
        StageInfo(
            stage_id=stage.stage_id,
            name=stage.name,
            order=stage.order,
            capability_contract_id=stage.capability_contract_id,
            is_required=stage.is_required,
        )
        for stage in list_stages()
    ]
    return StageListResponse(status="success", data=stages)
