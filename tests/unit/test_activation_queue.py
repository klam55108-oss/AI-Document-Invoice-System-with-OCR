"""Unit tests for configuration activation queue."""

import pytest

from core.configuration_service import ConfigurationService


@pytest.mark.asyncio
async def test_activation_queued_when_processing_active() -> None:
    """Activation should be queued while processing is active."""
    service = ConfigurationService()

    config = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v1"}],
        created_by="operator",
    )

    result = await service.activate_configuration(
        config.config_id,
        has_active_processing=True,
    )

    assert result.status == "queued"
    assert service.get_pending_activation() == config.config_id
