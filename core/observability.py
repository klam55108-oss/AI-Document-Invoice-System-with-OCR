"""Observability helpers for module configuration."""

from __future__ import annotations

from core.logging import get_logger

logger = get_logger(__name__)


def record_metric(name: str, value: float, **tags: str) -> None:
    """Record a lightweight metric event via structured logs."""
    logger.info("metric", metric_name=name, metric_value=value, **tags)


def record_event(event: str, **details: str) -> None:
    """Record a structured event for configuration operations."""
    logger.info(event, **details)


def record_module_failure(stage_id: str, module_id: str, error: str) -> None:
    """Record module failure event and metric."""
    record_event(
        "module_failure",
        stage_id=stage_id,
        module_id=module_id,
        error=error,
    )
    record_metric("module_failure", 1, stage_id=stage_id, module_id=module_id)
