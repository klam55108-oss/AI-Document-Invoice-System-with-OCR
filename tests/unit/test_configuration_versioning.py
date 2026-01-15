"""Unit tests for configuration versioning and rollback."""

import pytest

from core.configuration_service import ConfigurationService


@pytest.mark.asyncio
async def test_configuration_versions_increment() -> None:
    """New configurations should increment versions."""
    service = ConfigurationService()

    first = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v1"}],
        created_by="operator",
    )
    second = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v2"}],
        created_by="operator",
    )

    assert first.version == "v1"
    assert second.version == "v2"


@pytest.mark.asyncio
async def test_rollback_creates_new_active_version() -> None:
    """Rollback should create a new active version referencing prior selections."""
    service = ConfigurationService()

    config_one = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v1"}],
        created_by="operator",
    )
    config_two = await service.create_configuration(
        selections=[{"stage_id": "ocr", "module_id": "ocr-v2"}],
        created_by="operator",
    )

    await service.activate_configuration(config_two.config_id, has_active_processing=False)
    rollback_result = await service.rollback_configuration(
        config_one.config_id,
        actor="maintainer",
        has_active_processing=False,
    )

    assert rollback_result.status == "queued"
    active = await service.get_active_configuration()
    assert active is not None
    assert active.selections == config_one.selections
    assert active.version == "v3"
