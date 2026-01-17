"""OCR service for running and comparing providers."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from core.config import settings
from core.logging import get_logger
from core.ocr.configuration import ensure_provider_enabled, get_default_provider, resolve_provider
from sqlalchemy.ext.asyncio import AsyncSession

from core.ocr.repository import create_ocr_comparison, create_ocr_result
from ingestion.image_processor import process_image
from ingestion.pdf_processor import process_pdf_with_ocr

logger = get_logger(__name__)

_SUPPORTED_IMAGE_TYPES = {"jpg", "jpeg", "png", "webp", "avif"}


async def run_ocr(
    *,
    session: AsyncSession,
    input_path: Path,
    provider_id: str | None = None,
    allow_unavailable: bool = False,
):
    """Run OCR for a single input."""
    try:
        resolved_provider = resolve_provider(provider_id)
    except ValueError as exc:
        if not allow_unavailable:
            raise
        resolved_provider = (
            provider_id.strip().lower()
            if provider_id
            else get_default_provider()
        )
        return await create_ocr_result(
            session=session,
            input_id=str(input_path),
            provider_id=resolved_provider,
            extracted_text="",
            extracted_fields={},
            status="failed",
            error_message=str(exc),
            duration_ms=0,
        )
    start_time = time.time()
    status = "success"
    error_message = None
    extracted_text = ""
    extracted_fields: dict[str, Any] = {}

    try:
        file_type = input_path.suffix.lower().lstrip(".")
        if file_type in _SUPPORTED_IMAGE_TYPES:
            result = await process_image(input_path, provider_id=resolved_provider)
        elif file_type == "pdf":
            result = await process_pdf_with_ocr(input_path, provider_id=resolved_provider)
        else:
            raise ValueError(f"Unsupported OCR file type: {file_type}")

        extracted_text = result.get("text", "")
        extracted_fields = result.get("fields", {})
        if settings.OCR_INCLUDE_KEY_FIELDS and extracted_text:
            from brain.extractor import extract_invoice_data

            extraction = await extract_invoice_data(extracted_text, result.get("metadata"))
            extracted_fields = {
                "vendor_name": extraction.vendor_name,
                "invoice_number": extraction.invoice_number,
                "invoice_date": extraction.invoice_date.isoformat() if extraction.invoice_date else None,
                "due_date": extraction.due_date.isoformat() if extraction.due_date else None,
                "subtotal": float(extraction.subtotal) if extraction.subtotal else None,
                "tax_amount": float(extraction.tax_amount) if extraction.tax_amount else None,
                "total_amount": float(extraction.total_amount) if extraction.total_amount else None,
                "currency": extraction.currency,
            }
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        logger.error("OCR run failed", provider_id=resolved_provider, error=error_message)

    duration_ms = int((time.time() - start_time) * 1000)
    return await create_ocr_result(
        session=session,
        input_id=str(input_path),
        provider_id=resolved_provider,
        extracted_text=extracted_text,
        extracted_fields=extracted_fields,
        status=status,
        error_message=error_message,
        duration_ms=duration_ms,
    )


async def compare_ocr(
    *,
    session: AsyncSession,
    input_path: Path,
    provider_a_id: str,
    provider_b_id: str,
):
    """Compare two OCR providers for the same input."""
    if provider_a_id == provider_b_id:
        raise ValueError("Provider IDs must be different for comparison")

    provider_a = ensure_provider_enabled(provider_a_id)
    provider_b = ensure_provider_enabled(provider_b_id)

    result_a = await run_ocr(
        session=session,
        input_path=input_path,
        provider_id=provider_a,
        allow_unavailable=True,
    )
    result_b = await run_ocr(
        session=session,
        input_path=input_path,
        provider_id=provider_b,
        allow_unavailable=True,
    )

    summary = (
        f"{provider_a}: {result_a.status}, {provider_b}: {result_b.status}"
    )
    return await create_ocr_comparison(
        session=session,
        input_id=str(input_path),
        provider_a_result_id=str(result_a.id),
        provider_b_result_id=str(result_b.id),
        summary=summary,
    )
