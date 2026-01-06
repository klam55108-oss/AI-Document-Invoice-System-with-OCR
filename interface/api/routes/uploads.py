"""File upload route handlers."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.logging import get_logger
from core.models import Invoice
from ingestion.file_discovery import SUPPORTED_EXTENSIONS, get_file_type, is_supported_file
from ingestion.file_hasher import calculate_file_hash
from ingestion.orchestrator import process_invoice_file
from interface.api.schemas import (
    ErrorDetail,
    ErrorResponse,
    UploadData,
    UploadItem,
    UploadResponse,
    UploadStatusData,
    UploadStatusResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/uploads", tags=["Uploads"])

# Constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_SUBFOLDER = "uploads"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and parent directory references
    sanitized = filename.replace("..", "").replace("/", "").replace("\\", "")
    # Remove any remaining dangerous characters
    sanitized = "".join(c for c in sanitized if c.isprintable() and c not in ['<', '>', ':', '"', '|', '?', '*'])
    return sanitized or "uploaded_file"


def validate_subfolder(subfolder: str) -> bool:
    """Validate subfolder name to prevent path traversal.

    Args:
        subfolder: Subfolder name

    Returns:
        True if valid, False otherwise
    """
    if not subfolder:
        return False
    # Check for path traversal attempts
    if ".." in subfolder or "/" in subfolder or "\\" in subfolder:
        return False
    # Check for empty or only whitespace
    if not subfolder.strip():
        return False
    return True


async def validate_file(file: UploadFile) -> tuple[bool, str | None]:
    """Validate uploaded file.

    Args:
        file: Uploaded file object

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file type
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {file_ext}. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"

    # Check file size
    # Read file content to get size (for multipart uploads, we need to read it)
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        return False, f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"

    if file_size == 0:
        return False, "File is empty"

    return True, None


@router.post("", response_model=UploadResponse, status_code=202)
async def upload_files(
    files: Annotated[list[UploadFile], File(description="One or more invoice files to upload")],
    subfolder: Annotated[str | None, Form(description="Subfolder within data/ directory")] = None,
    group: Annotated[str | None, Form(description="Group/batch identifier")] = None,
    category: Annotated[str | None, Form(description="Category for organizing uploads")] = None,
    force_reprocess: Annotated[bool, Form(description="Force reprocessing even if file hash exists")] = False,
    session: AsyncSession = Depends(get_session),
) -> UploadResponse:
    """Upload one or more invoice files for processing.

    Files are validated, stored, and automatically processed.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    data_dir = Path("data")
    upload_subfolder = subfolder or DEFAULT_SUBFOLDER
    
    # Validate subfolder name
    if not validate_subfolder(upload_subfolder):
        raise HTTPException(
            status_code=400,
            detail="Invalid subfolder name. Subfolder cannot contain path separators or parent directory references.",
        )
    
    upload_dir = data_dir / upload_subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting file upload", file_count=len(files), subfolder=upload_subfolder)

    upload_results: list[UploadItem] = []
    successful = 0
    failed = 0
    skipped = 0

    for file in files:
        file_name = file.filename or "unknown"
        sanitized_name = sanitize_filename(file_name)

        try:
            # Validate file
            is_valid, error_msg = await validate_file(file)
            if not is_valid:
                upload_results.append(
                    UploadItem(
                        file_name=file_name,
                        status="failed",
                        error_message=error_msg,
                    )
                )
                failed += 1
                continue

            # Read file content
            content = await file.read()
            file_size = len(content)

            # Save file to disk
            file_path = upload_dir / sanitized_name
            # Handle filename conflicts by appending a number
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = upload_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            with open(file_path, "wb") as f:
                f.write(content)

            logger.info("File saved", path=str(file_path), size=file_size, filename=file_name)

            # Calculate file hash
            file_hash = calculate_file_hash(file_path)

            # Check for duplicate
            existing_invoice_stmt = (
                select(Invoice)
                .where(Invoice.file_hash == file_hash)
                .order_by(Invoice.version.desc())
                .limit(1)
            )
            result = await session.execute(existing_invoice_stmt)
            existing_invoice = result.scalar_one_or_none()

            if existing_invoice and not force_reprocess:
                upload_results.append(
                    UploadItem(
                        file_name=file_name,
                        status="duplicate",
                        file_path=str(file_path.relative_to(data_dir)),
                        file_size=file_size,
                        error_message="File with same content already exists. Use force_reprocess=true to reprocess.",
                    )
                )
                skipped += 1
                # Remove the duplicate file we just saved
                file_path.unlink()
                continue

            # Create upload metadata
            upload_metadata = {
                "subfolder": upload_subfolder,
                "upload_source": "web-ui",
                "uploaded_at": datetime.utcnow().isoformat() + "Z",
            }
            if group:
                upload_metadata["group"] = group
            if category:
                upload_metadata["category"] = category

            # Process invoice file
            try:
                invoice = await process_invoice_file(
                    file_path=file_path,
                    data_dir=data_dir,
                    session=session,
                    force_reprocess=force_reprocess,
                    upload_metadata=upload_metadata,
                )

                await session.commit()

                upload_results.append(
                    UploadItem(
                        file_name=file_name,
                        invoice_id=str(invoice.id),
                        status="processing",
                        file_path=str(file_path.relative_to(data_dir)),
                        file_size=file_size,
                    )
                )
                successful += 1

            except Exception as e:
                await session.rollback()
                logger.error("Processing failed", file_name=file_name, error=str(e), exc_info=True)
                upload_results.append(
                    UploadItem(
                        file_name=file_name,
                        status="failed",
                        file_path=str(file_path.relative_to(data_dir)),
                        file_size=file_size,
                        error_message=f"Processing failed: {str(e)}",
                    )
                )
                failed += 1

        except Exception as e:
            logger.error("Upload failed", file_name=file_name, error=str(e), exc_info=True)
            upload_results.append(
                UploadItem(
                    file_name=file_name,
                    status="failed",
                    error_message=f"Upload failed: {str(e)}",
                )
            )
            failed += 1
    
    logger.info(
        "Upload batch completed",
        total=len(files),
        successful=successful,
        failed=failed,
        skipped=skipped,
    )

    return UploadResponse(
        status="success",
        data=UploadData(
            uploads=upload_results,
            total=len(files),
            successful=successful,
            failed=failed,
            skipped=skipped,
        ),
    )


@router.get("/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> UploadStatusResponse:
    """Get the current status of an upload and its processing.

    Args:
        upload_id: Invoice ID (from upload response)
        session: Database session

    Returns:
        Upload status information
    """
    # Get invoice
    invoice_query = select(Invoice).where(Invoice.id == upload_id)
    result = await session.execute(invoice_query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice not found: {upload_id}")

    from interface.api.schemas import UploadMetadata

    upload_metadata = None
    if invoice.upload_metadata:
        upload_metadata = UploadMetadata(**invoice.upload_metadata)

    return UploadStatusResponse(
        status="success",
        data=UploadStatusData(
            invoice_id=str(invoice.id),
            file_name=invoice.file_name,
            file_path=invoice.file_path,
            processing_status=invoice.processing_status.value,
            upload_metadata=upload_metadata,
            error_message=invoice.error_message,
        ),
    )
