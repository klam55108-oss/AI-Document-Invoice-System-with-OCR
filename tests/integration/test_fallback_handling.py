"""Integration test for module failure fallback handling."""

import pytest

from core.configuration_service import ConfigurationService
from ingestion.orchestrator import apply_fallback_for_stage


@pytest.mark.asyncio
async def test_fallback_used_on_failure() -> None:
    """Fallback module should be used when stage fails."""
    service = ConfigurationService()
    await service.set_fallback_policy(stage_id="ocr", fallback_module_id="ocr-fallback")

    result = await apply_fallback_for_stage(
        stage_id="ocr",
        error="failure",
        service=service,
    )

    assert result == "ocr-fallback"
