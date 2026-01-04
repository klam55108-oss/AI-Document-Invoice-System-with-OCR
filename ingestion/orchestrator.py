"""File processing orchestration and version tracking."""

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from brain.extractor import extract_invoice_data
from brain.schemas import ExtractedDataSchema
from brain.validator import get_validation_framework
from core.database import get_session
from core.logging import get_logger
from core.models import ExtractedData, Invoice, ProcessingJob, ProcessingStatus, ValidationResult, ValidationStatus
from ingestion.excel_processor import process_excel
from ingestion.file_discovery import get_file_type, is_supported_file
from ingestion.file_hasher import calculate_file_hash
from ingestion.image_processor import process_image
from ingestion.pdf_processor import process_pdf

logger = get_logger(__name__)


async def process_invoice_file(
    file_path: Path, data_dir: Path, session: AsyncSession, force_reprocess: bool = False
) -> Invoice:
    """Process an invoice file end-to-end.

    Args:
        file_path: Path to invoice file
        data_dir: Base data directory
        session: Database session
        force_reprocess: Force reprocessing even if file hash exists

    Returns:
        Invoice model instance

    Raises:
        ValueError: If file is not supported
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not is_supported_file(file_path):
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    logger.info("Processing invoice file", path=str(file_path))

    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    file_size = file_path.stat().st_size
    file_type = get_file_type(file_path)

    # Check for existing invoice with same hash
    from sqlalchemy import select

    existing_invoice_stmt = select(Invoice).where(Invoice.file_hash == file_hash)
    result = await session.execute(existing_invoice_stmt)
    existing_invoice = result.scalar_one_or_none()

    # Determine version
    if existing_invoice and not force_reprocess:
        version = existing_invoice.version + 1
        logger.info("Reprocessing existing file", hash=file_hash[:8], version=version)
    else:
        version = 1

    # Encrypt file if encryption is enabled
    encrypted_file_path = None
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key:
        try:
            encryption = FileEncryption(encryption_key)
            # Store encrypted file in a secure location
            encrypted_dir = Path("data/encrypted")
            encrypted_dir.mkdir(exist_ok=True)
            encrypted_dest = encrypted_dir / f"{file_hash}.encrypted"
            encryption.encrypt_file(file_path, encrypted_dest)
            encrypted_file_path = str(encrypted_dest.relative_to(data_dir))
            logger.info("File encrypted", original=str(file_path), encrypted=str(encrypted_dest))
        except Exception as e:
            logger.warning("File encryption failed, continuing without encryption", error=str(e))

    # Create invoice record
    invoice = Invoice(
        id=uuid.uuid4(),
        file_path=str(file_path.relative_to(data_dir)),
        file_name=file_path.name,
        file_hash=file_hash,
        file_size=file_size,
        file_type=file_type,
        version=version,
        processing_status=ProcessingStatus.PROCESSING,
        encrypted_file_path=encrypted_file_path,
    )

    session.add(invoice)
    await session.flush()  # Get invoice ID

    try:
        # Process file based on type
        if file_type == "pdf":
            processed_data = await process_pdf(file_path)
        elif file_type in {"xlsx", "csv"}:
            processed_data = await process_excel(file_path)
        elif file_type in {"jpg", "png"}:
            processed_data = await process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Extract structured data
        raw_text = processed_data.get("text", "")
        extracted_data = await extract_invoice_data(raw_text, processed_data.get("metadata"))

        # Create extracted data record
        extracted_record = ExtractedData(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            vendor_name=extracted_data.vendor_name,
            invoice_number=extracted_data.invoice_number,
            invoice_date=extracted_data.invoice_date,
            due_date=extracted_data.due_date,
            subtotal=extracted_data.subtotal,
            tax_amount=extracted_data.tax_amount,
            tax_rate=extracted_data.tax_rate,
            total_amount=extracted_data.total_amount,
            currency=extracted_data.currency,
            line_items=extracted_data.line_items,
            raw_text=extracted_data.raw_text,
            extraction_confidence=extracted_data.extraction_confidence,
        )

        session.add(extracted_record)
        await session.flush()

        # Run validation rules
        validation_framework = get_validation_framework()
        validation_results = await validation_framework.validate(extracted_data)

        # Store validation results
        for result in validation_results:
            validation_record = ValidationResult(
                id=uuid.uuid4(),
                invoice_id=invoice.id,
                rule_name=result.rule_name,
                rule_description=result.rule_description,
                status=ValidationStatus(result.status),
                expected_value=result.expected_value,
                actual_value=result.actual_value,
                tolerance=result.tolerance,
                error_message=result.error_message,
            )
            session.add(validation_record)

        # Update invoice status
        invoice.processing_status = ProcessingStatus.COMPLETED
        from datetime import datetime

        invoice.processed_at = datetime.utcnow()

        logger.info(
            "Invoice processing completed",
            invoice_id=str(invoice.id),
            validations=len(validation_results),
            failed_validations=sum(1 for r in validation_results if r.status == "failed"),
        )

        return invoice

    except Exception as e:
        # Fail-fast: Log error, mark job as failed, stop processing this file
        # But don't raise - allow caller to continue with other files
        import traceback

        error_traceback = traceback.format_exc()
        logger.error(
            "Invoice processing failed",
            invoice_id=str(invoice.id),
            file_path=str(file_path),
            error=str(e),
            traceback=error_traceback,
        )

        invoice.processing_status = ProcessingStatus.FAILED
        invoice.error_message = str(e)

        # Create failed processing job record
        from core.models import ProcessingJob, JobType, ExecutionType
        from datetime import datetime

        failed_job = ProcessingJob(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            job_type=JobType.FILE_INGESTION,
            execution_type=ExecutionType.ASYNC_COROUTINE,
            status=ProcessingStatus.FAILED,
            error_message=str(e),
            error_traceback=error_traceback,
            completed_at=datetime.utcnow(),
        )
        session.add(failed_job)

        # Note: We don't raise here - this allows the caller to continue processing other files
        # The invoice is marked as failed and can be reviewed in the dashboard
        return invoice

