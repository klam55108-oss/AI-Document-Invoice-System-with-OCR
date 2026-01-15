"""Unit tests for observability helpers."""

from core.observability import record_event, record_metric


def test_record_event_emits_log() -> None:
    """record_event should execute without error."""
    assert record_event("config_swapped", config_id="abc") is None


def test_record_metric_emits_log() -> None:
    """record_metric should execute without error."""
    assert record_metric("config_activation", 1.0, outcome="queued") is None
