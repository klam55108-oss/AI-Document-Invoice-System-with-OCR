"""Unit tests for fallback policy evaluation."""

import pytest

from core.configuration_service import ConfigurationService


@pytest.mark.asyncio
async def test_fallback_policy_returns_module() -> None:
    """Fallback policy returns fallback module when configured."""
    service = ConfigurationService()
    await service.set_fallback_policy(stage_id="ocr", fallback_module_id="ocr-fallback")

    fallback = await service.evaluate_fallback(stage_id="ocr", error="fail")

    assert fallback == "ocr-fallback"


@pytest.mark.asyncio
async def test_fallback_policy_none_when_missing() -> None:
    """Fallback policy returns None when not configured."""
    service = ConfigurationService()
    fallback = await service.evaluate_fallback(stage_id="ocr", error="fail")

    assert fallback is None
