"""OCR persistence helpers."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import OcrComparison, OcrResult


async def create_ocr_result(
    *,
    session: AsyncSession,
    input_id: str,
    provider_id: str,
    extracted_text: str,
    extracted_fields: dict[str, Any],
    status: str,
    error_message: str | None,
    duration_ms: int | None,
) -> OcrResult:
    """Persist OCR result record."""
    record = OcrResult(
        input_id=input_id,
        provider_id=provider_id,
        extracted_text=extracted_text,
        extracted_fields=extracted_fields,
        status=status,
        error_message=error_message,
        duration_ms=duration_ms,
    )
    session.add(record)
    await session.flush()
    return record


async def get_ocr_result(session: AsyncSession, result_id: str) -> OcrResult | None:
    """Fetch OCR result record by id."""
    query = select(OcrResult).where(OcrResult.id == result_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_ocr_comparison(
    *,
    session: AsyncSession,
    input_id: str,
    provider_a_result_id: str,
    provider_b_result_id: str,
    summary: str | None,
) -> OcrComparison:
    """Persist OCR comparison record."""
    record = OcrComparison(
        input_id=input_id,
        provider_a_result_id=provider_a_result_id,
        provider_b_result_id=provider_b_result_id,
        summary=summary,
    )
    session.add(record)
    await session.flush()
    return record


async def get_ocr_comparison(
    session: AsyncSession, comparison_id: str
) -> OcrComparison | None:
    """Fetch OCR comparison record by id."""
    query = select(OcrComparison).where(OcrComparison.id == comparison_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()
