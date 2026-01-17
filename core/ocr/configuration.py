"""Runtime OCR provider configuration."""
from __future__ import annotations

from dataclasses import dataclass

from core.config import settings
from core.logging import get_logger
from core.ocr.providers import list_provider_ids, provider_status

logger = get_logger(__name__)


@dataclass(slots=True)
class OcrProviderConfig:
    """Mutable OCR provider configuration."""

    default_provider: str
    enabled_providers: set[str]


def _normalize_provider_id(provider_id: str) -> str:
    return provider_id.strip().lower()


def _parse_enabled_providers(raw_value: str) -> set[str]:
    if not raw_value:
        return set()
    return {_normalize_provider_id(value) for value in raw_value.split(",") if value.strip()}


_config = OcrProviderConfig(
    default_provider=_normalize_provider_id(settings.OCR_DEFAULT_PROVIDER),
    enabled_providers=_parse_enabled_providers(settings.OCR_ENABLED_PROVIDERS),
)

if not _config.enabled_providers:
    _config.enabled_providers = {_config.default_provider}
elif _config.default_provider not in _config.enabled_providers:
    _config.enabled_providers.add(_config.default_provider)


def get_enabled_providers() -> list[str]:
    """Return enabled provider IDs."""
    return sorted(_config.enabled_providers)


def get_default_provider() -> str:
    """Return the default provider ID."""
    return _config.default_provider


def set_enabled_providers(provider_ids: list[str]) -> None:
    """Set enabled provider IDs."""
    normalized = {_normalize_provider_id(provider_id) for provider_id in provider_ids}
    _validate_provider_ids(normalized)
    _config.enabled_providers = normalized
    if _config.default_provider not in _config.enabled_providers:
        _config.default_provider = sorted(_config.enabled_providers)[0]
    logger.info("Updated enabled OCR providers", enabled_providers=sorted(_config.enabled_providers))


def set_default_provider(provider_id: str) -> None:
    """Set the default provider ID."""
    normalized = _normalize_provider_id(provider_id)
    _validate_provider_ids({normalized})
    if normalized not in _config.enabled_providers:
        raise ValueError("Default provider must be enabled")
    _config.default_provider = normalized
    logger.info("Updated default OCR provider", default_provider=_config.default_provider)


def resolve_provider(provider_id: str | None) -> str:
    """Resolve provider ID, applying default and enabled checks."""
    resolved = _normalize_provider_id(provider_id) if provider_id else _config.default_provider
    _validate_provider_ids({resolved})
    if resolved not in _config.enabled_providers:
        raise ValueError(f"Provider is not enabled: {resolved}")
    if provider_status(resolved) != "available":
        raise ValueError(f"Provider is unavailable: {resolved}")
    return resolved


def ensure_provider_enabled(provider_id: str) -> str:
    """Validate provider exists and is enabled (availability not enforced)."""
    resolved = _normalize_provider_id(provider_id)
    _validate_provider_ids({resolved})
    if resolved not in _config.enabled_providers:
        raise ValueError(f"Provider is not enabled: {resolved}")
    return resolved


def _validate_provider_ids(provider_ids: set[str]) -> None:
    available = set(list_provider_ids())
    unknown = sorted(provider_ids - available)
    if unknown:
        raise ValueError(f"Unknown OCR providers: {', '.join(unknown)}")
