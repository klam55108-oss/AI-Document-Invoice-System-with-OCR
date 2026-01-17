"""Unit tests for OCR provider configuration."""
import pytest

from core.ocr import configuration as ocr_config


def test_resolve_provider_uses_default(monkeypatch) -> None:
    """Resolve provider defaults when none provided."""
    monkeypatch.setattr(ocr_config, "provider_status", lambda _: "available")
    ocr_config.set_enabled_providers(["paddleocr"])
    ocr_config.set_default_provider("paddleocr")
    assert ocr_config.resolve_provider(None) == "paddleocr"


def test_resolve_provider_rejects_disabled(monkeypatch) -> None:
    """Resolve provider rejects disabled provider."""
    monkeypatch.setattr(ocr_config, "provider_status", lambda _: "available")
    ocr_config.set_enabled_providers(["paddleocr"])
    with pytest.raises(ValueError):
        ocr_config.resolve_provider("deepseek-ocr")
