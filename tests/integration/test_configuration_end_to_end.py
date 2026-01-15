"""Integration test for configuration + fallback flow."""

import pytest

from core.configuration_service import ConfigurationService
from ingestion.orchestrator import apply_fallback_for_stage


@pytest.mark.asyncio
async def test_configuration_with_fallback_flow() -> None:
    """Create configuration, activate, and apply fallback on failure."""
    service = ConfigurationService()
    config = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v1"}],
        created_by="operator",
    )
    await service.activate_configuration(config.config_id, has_active_processing=False)
    await service.set_fallback_policy(stage_id="ocr", fallback_module_id="ocr-fallback")

    fallback = await apply_fallback_for_stage(stage_id="ocr", error="fail", service=service)

    assert fallback == "ocr-fallback"
