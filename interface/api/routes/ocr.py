"""OCR provider routes."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.ocr.configuration import (
    get_default_provider,
    get_enabled_providers,
    set_default_provider,
    set_enabled_providers,
)
from core.ocr.providers import get_provider_metadata, list_provider_ids, provider_status
from core.ocr.service import compare_ocr, run_ocr
from core.ocr.repository import (
    get_ocr_comparison as fetch_ocr_comparison,
    get_ocr_result as fetch_ocr_result,
)
from interface.api.dependencies import require_operator_or_maintainer
from interface.api.schemas import (
    OcrComparison,
    OcrComparisonResponse,
    OcrCompareRequest,
    OcrProvider,
    OcrProviderListResponse,
    OcrResult,
    OcrResultResponse,
    OcrRunRequest,
)

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])


def _resolve_input_path(input_id: str) -> Path:
    data_dir = Path("data").resolve()
    raw_path = Path(input_id)
    if raw_path.is_absolute():
        try:
            raw_path.relative_to(data_dir)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input path must be within data directory",
            )
        resolved = raw_path
    else:
        resolved = (data_dir / raw_path).resolve()
        try:
            resolved.relative_to(data_dir)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input path (path traversal detected)",
            )
    if not resolved.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Input file not found: {input_id}",
        )
    return resolved


def _to_result_schema(record) -> OcrResult:
    return OcrResult(
        result_id=str(record.id),
        input_id=record.input_id,
        provider_id=record.provider_id,
        extracted_text=record.extracted_text,
        extracted_fields=record.extracted_fields,
        status=record.status,
        error_message=record.error_message,
        duration_ms=record.duration_ms,
        created_at=record.created_at,
    )


@router.get("/providers", response_model=OcrProviderListResponse)
async def list_providers() -> OcrProviderListResponse:
    """List OCR providers."""
    default_provider = get_default_provider()
    enabled_providers = set(get_enabled_providers())
    providers = []
    for provider_id in list_provider_ids():
        metadata = get_provider_metadata(provider_id)
        providers.append(
            OcrProvider(
                provider_id=provider_id,
                name=metadata["name"],
                is_enabled=provider_id in enabled_providers,
                is_default=provider_id == default_provider,
                status=provider_status(provider_id),
                supported_formats=metadata["supported_formats"],
            )
        )
    return OcrProviderListResponse(status="success", data=providers)


@router.patch("/providers/default", response_model=OcrProviderListResponse)
async def update_default_provider(
    payload: dict,
    _: str = Depends(require_operator_or_maintainer),
) -> OcrProviderListResponse:
    """Set default OCR provider (admin)."""
    provider_id = payload.get("provider_id")
    if not provider_id:
        raise HTTPException(status_code=400, detail="provider_id is required")
    try:
        set_default_provider(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await list_providers()


@router.patch("/providers/enabled", response_model=OcrProviderListResponse)
async def update_enabled_providers(
    payload: dict,
    _: str = Depends(require_operator_or_maintainer),
) -> OcrProviderListResponse:
    """Set enabled OCR providers (admin)."""
    provider_ids = payload.get("provider_ids")
    if not provider_ids:
        raise HTTPException(status_code=400, detail="provider_ids is required")
    try:
        set_enabled_providers(provider_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await list_providers()


@router.post("/run", response_model=OcrResultResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_ocr_request(
    payload: OcrRunRequest,
    session: AsyncSession = Depends(get_session),
) -> OcrResultResponse:
    """Run OCR for a single input."""
    input_path = _resolve_input_path(payload.input_id)
    try:
        record = await run_ocr(
            session=session,
            input_path=input_path,
            provider_id=payload.provider_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OcrResultResponse(status="success", data=_to_result_schema(record))


@router.post("/compare", response_model=OcrComparisonResponse, status_code=status.HTTP_202_ACCEPTED)
async def compare_ocr_request(
    payload: OcrCompareRequest,
    session: AsyncSession = Depends(get_session),
) -> OcrComparisonResponse:
    """Compare OCR providers for a single input."""
    input_path = _resolve_input_path(payload.input_id)
    try:
        comparison = await compare_ocr(
            session=session,
            input_path=input_path,
            provider_a_id=payload.provider_a_id,
            provider_b_id=payload.provider_b_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result_a = await fetch_ocr_result(session, str(comparison.provider_a_result_id))
    result_b = await fetch_ocr_result(session, str(comparison.provider_b_result_id))
    response = OcrComparison(
        comparison_id=str(comparison.id),
        input_id=comparison.input_id,
        provider_a_result_id=str(comparison.provider_a_result_id),
        provider_b_result_id=str(comparison.provider_b_result_id),
        provider_a_result=_to_result_schema(result_a) if result_a else None,
        provider_b_result=_to_result_schema(result_b) if result_b else None,
        summary=comparison.summary,
        created_at=comparison.created_at,
    )
    return OcrComparisonResponse(status="success", data=response)


@router.get("/results/{result_id}", response_model=OcrResultResponse)
async def get_ocr_result(
    result_id: str,
    session: AsyncSession = Depends(get_session),
) -> OcrResultResponse:
    """Get OCR result by id."""
    record = await fetch_ocr_result(session, result_id)
    if not record:
        raise HTTPException(status_code=404, detail="OCR result not found")
    return OcrResultResponse(status="success", data=_to_result_schema(record))


@router.get("/comparisons/{comparison_id}", response_model=OcrComparisonResponse)
async def get_ocr_comparison(
    comparison_id: str,
    session: AsyncSession = Depends(get_session),
) -> OcrComparisonResponse:
    """Get OCR comparison by id."""
    record = await fetch_ocr_comparison(session, comparison_id)
    if not record:
        raise HTTPException(status_code=404, detail="OCR comparison not found")
    result_a = await fetch_ocr_result(session, str(record.provider_a_result_id))
    result_b = await fetch_ocr_result(session, str(record.provider_b_result_id))
    comparison = OcrComparison(
        comparison_id=str(record.id),
        input_id=record.input_id,
        provider_a_result_id=str(record.provider_a_result_id),
        provider_b_result_id=str(record.provider_b_result_id),
        provider_a_result=_to_result_schema(result_a) if result_a else None,
        provider_b_result=_to_result_schema(result_b) if result_b else None,
        summary=record.summary,
        created_at=record.created_at,
    )
    return OcrComparisonResponse(status="success", data=comparison)
