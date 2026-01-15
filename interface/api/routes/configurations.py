"""Configuration management routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.configuration_service import ConfigurationRecord, get_configuration_service
from core.configuration_validation import ValidationResult
from core.logging import get_logger
from interface.api.dependencies import require_operator_or_maintainer
from interface.api.schemas import (
    ConfigActivationResult,
    ConfigRollbackResult,
    ConfigValidationResult,
    ConfigurationActivationResponse,
    ConfigurationDetailResponse,
    ConfigurationListResponse,
    ConfigurationRollbackResponse,
    ConfigurationValidationResponse,
    ModuleConfigurationCreate,
    ModuleConfigurationInfo,
)

router = APIRouter(prefix="/api/v1/configurations", tags=["configurations"])
logger = get_logger(__name__)


def _to_config_info(record: ConfigurationRecord) -> ModuleConfigurationInfo:
    return ModuleConfigurationInfo(
        config_id=record.config_id,
        version=record.version,
        status=record.status,
        created_by=record.created_by,
        created_at=record.created_at,
        activated_at=record.activated_at,
        selections=record.selections,
    )


@router.get("", response_model=ConfigurationListResponse)
async def list_configurations() -> ConfigurationListResponse:
    """List configurations."""
    service = get_configuration_service()
    configs = [ _to_config_info(record) for record in await service.list_configurations() ]
    return ConfigurationListResponse(status="success", data=configs)


@router.post("", response_model=ConfigurationDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_configuration(
    payload: ModuleConfigurationCreate,
    _: str = Depends(require_operator_or_maintainer),
) -> ConfigurationDetailResponse:
    """Create a configuration draft."""
    service = get_configuration_service()
    record = await service.create_configuration(
        selections=[selection.model_dump() for selection in payload.selections],
        created_by="operator",
    )
    logger.info("Configuration created", config_id=record.config_id, version=record.version)
    return ConfigurationDetailResponse(status="success", data=_to_config_info(record))


@router.post("/validate", response_model=ConfigurationValidationResponse)
async def validate_configuration(
    payload: ModuleConfigurationCreate,
    _: str = Depends(require_operator_or_maintainer),
) -> ConfigurationValidationResponse:
    """Validate a configuration without activation."""
    service = get_configuration_service()
    result: ValidationResult = await service.validate_configuration(
        selections=[selection.model_dump() for selection in payload.selections]
    )
    response = ConfigValidationResult(
        is_valid=result.is_valid,
        errors=result.errors,
        warnings=result.warnings,
    )
    if not result.is_valid:
        logger.warning("Configuration validation failed", errors=result.errors)
    return ConfigurationValidationResponse(status="success", data=response)


@router.get("/active", response_model=ConfigurationDetailResponse)
async def get_active_configuration() -> ConfigurationDetailResponse:
    """Get the active configuration."""
    service = get_configuration_service()
    record = await service.get_active_configuration()
    if not record:
        raise HTTPException(status_code=404, detail="No active configuration")
    return ConfigurationDetailResponse(status="success", data=_to_config_info(record))


@router.get("/{config_id}", response_model=ConfigurationDetailResponse)
async def get_configuration(config_id: str) -> ConfigurationDetailResponse:
    """Get configuration by ID."""
    service = get_configuration_service()
    record = await service.get_configuration(config_id)
    if not record:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return ConfigurationDetailResponse(status="success", data=_to_config_info(record))


@router.post("/{config_id}/activate", response_model=ConfigurationActivationResponse)
async def activate_configuration(
    config_id: str,
    processing_active: bool = Query(default=False, description="Whether processing is active"),
    _: str = Depends(require_operator_or_maintainer),
) -> ConfigurationActivationResponse:
    """Activate a configuration."""
    service = get_configuration_service()
    record = await service.get_configuration(config_id)
    if not record:
        raise HTTPException(status_code=404, detail="Configuration not found")

    validation = await service.validate_configuration(selections=record.selections)
    if not validation.is_valid:
        logger.warning("Configuration activation blocked", config_id=config_id, errors=validation.errors)
        raise HTTPException(status_code=400, detail="Configuration failed validation")

    result = await service.activate_configuration(
        config_id=config_id, has_active_processing=processing_active
    )
    response = ConfigActivationResult(status=result.status, message=result.message)
    return ConfigurationActivationResponse(status="success", data=response)


@router.post("/{config_id}/rollback", response_model=ConfigurationRollbackResponse)
async def rollback_configuration(
    config_id: str,
    processing_active: bool = Query(default=False, description="Whether processing is active"),
    _: str = Depends(require_operator_or_maintainer),
) -> ConfigurationRollbackResponse:
    """Rollback to a prior configuration version."""
    service = get_configuration_service()
    result = await service.rollback_configuration(
        config_id=config_id,
        actor="maintainer",
        has_active_processing=processing_active,
    )
    if result.status == "rejected":
        logger.warning("Configuration rollback rejected", config_id=config_id, message=result.message)
        raise HTTPException(status_code=400, detail=result.message)
    response = ConfigRollbackResult(status=result.status, message=result.message)
    return ConfigurationRollbackResponse(status="success", data=response)
