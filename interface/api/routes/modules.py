"""Module registry routes."""

from fastapi import APIRouter

from core.module_registry import list_modules
from interface.api.schemas import ModuleInfo, ModuleListResponse

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])


@router.get("", response_model=ModuleListResponse)
async def list_available_modules() -> ModuleListResponse:
    """List registered modules."""
    modules = [
        ModuleInfo(
            module_id=module.module_id,
            name=module.name,
            stage_id=module.stage_id,
            capability_contract_id=module.capability_contract_id,
            status=module.status,
            is_fallback=module.is_fallback,
        )
        for module in list_modules()
    ]
    return ModuleListResponse(status="success", data=modules)
