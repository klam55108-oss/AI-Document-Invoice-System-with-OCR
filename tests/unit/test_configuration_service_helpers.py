"""Additional unit tests for configuration service coverage."""

import pytest

from core.configuration_service import ConfigurationService


@pytest.mark.asyncio
async def test_list_configurations_empty() -> None:
    """List returns empty when no configs exist."""
    service = ConfigurationService()
    configs = await service.list_configurations()
    assert configs == []


@pytest.mark.asyncio
async def test_pending_activation_cleared_on_activation() -> None:
    """Pending activation should clear after activation is applied."""
    service = ConfigurationService()
    config = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v1"}],
        created_by="operator",
    )

    await service.activate_configuration(config.config_id, has_active_processing=True)
    assert service.get_pending_activation() == config.config_id

    await service.activate_configuration(config.config_id, has_active_processing=False)
    assert service.get_pending_activation() is None
