"""In-memory OCR result storage."""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any


@dataclass(slots=True)
class OcrResultRecord:
    """OCR result record."""

    result_id: str
    input_id: str
    provider_id: str
    extracted_text: str
    extracted_fields: dict[str, Any]
    status: str
    error_message: str | None
    duration_ms: int
    created_at: datetime


@dataclass(slots=True)
class OcrComparisonRecord:
    """OCR comparison record."""

    comparison_id: str
    input_id: str
    provider_a_result_id: str
    provider_b_result_id: str
    summary: str | None
    created_at: datetime


_results: dict[str, OcrResultRecord] = {}
_comparisons: dict[str, OcrComparisonRecord] = {}
_lock = asyncio.Lock()


async def save_result(record: OcrResultRecord) -> None:
    """Persist OCR result record."""
    async with _lock:
        _results[record.result_id] = record


async def save_comparison(record: OcrComparisonRecord) -> None:
    """Persist OCR comparison record."""
    async with _lock:
        _comparisons[record.comparison_id] = record


async def get_result(result_id: str) -> OcrResultRecord | None:
    """Fetch OCR result record."""
    async with _lock:
        return _results.get(result_id)


async def get_comparison(comparison_id: str) -> OcrComparisonRecord | None:
    """Fetch OCR comparison record."""
    async with _lock:
        return _comparisons.get(comparison_id)


def new_result_id() -> str:
    """Create a new OCR result id."""
    return str(uuid.uuid4())


def new_comparison_id() -> str:
    """Create a new OCR comparison id."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)
