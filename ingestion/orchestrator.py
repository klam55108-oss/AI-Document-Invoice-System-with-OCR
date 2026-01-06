"""File processing orchestration and version tracking."""

import os
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from brain.extractor import extract_invoice_data
from brain.schemas import ExtractedDataSchema
from brain.validator import get_validation_framework
from core.database import get_session
from core.encryption import FileEncryption
from core.logging import get_logger
from core.models import ExtractedData, Invoice, ProcessingJob, ProcessingStatus, ValidationResult, ValidationStatus
from ingestion.excel_processor import process_excel
from ingestion.file_discovery import get_file_type, is_supported_file
from ingestion.file_hasher import calculate_file_hash
from ingestion.image_processor import process_image
from ingestion.pdf_processor import process_pdf

logger = get_logger(__name__)


async def process_invoice_file(
    file_path: Path,
    data_dir: Path,
    session: AsyncSession,
    force_reprocess: bool = False,
    upload_metadata: dict | None = None,
    category: str | None = None,
    group: str | None = None,
    job_id: uuid.UUID | None = None,
) -> Invoice:
    """Process an invoice file end-to-end.

    Args:
        file_path: Path to invoice file
        data_dir: Base data directory
        session: Database session
        force_reprocess: Force reprocessing even if file hash exists
        upload_metadata: Optional metadata about the upload (subfolder, group, category, etc.)

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

    # Check for existing invoice with same hash (get the latest version)
    from sqlalchemy import select

    existing_invoice_stmt = (
        select(Invoice)
        .where(Invoice.file_hash == file_hash)
        .order_by(Invoice.version.desc())
        .limit(1)
    )
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

    # Determine group/category from path if not provided
    # e.g. data/grok/9.png -> group = grok
    if not group and len(file_path.relative_to(data_dir).parts) > 1:
        group = file_path.relative_to(data_dir).parts[0]
    
    # Create invoice record
    invoice = Invoice(
        id=uuid.uuid4(),
        storage_path=str(file_path.relative_to(data_dir)),
        file_name=file_path.name,
        category=category,
        group=group,
        job_id=job_id,
        file_hash=file_hash,
        file_size=file_size,
        file_type=file_type,
        version=version,
        processing_status=ProcessingStatus.PROCESSING,
        encrypted_file_path=encrypted_file_path,
        upload_metadata=upload_metadata,
    )

    session.add(invoice)
    await session.flush()  # Get invoice ID

    try:
        # Process file based on type
        if file_type == "pdf":
            processed_data = await process_pdf(file_path)
        elif file_type in {"xlsx", "csv"}:
            processed_data = await process_excel(file_path)
        elif file_type in {"jpg", "png", "webp", "avif"}:
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

        # Self-correction intelligence: If critical validations failed, try refining
        failed_validations = [r for r in validation_results if r.status == "failed"]
        if failed_validations:
            logger.info(
                "Triggering self-correction refinement",
                invoice_id=str(invoice.id),
                failed_count=len(failed_validations),
            )
            from brain.extractor import refine_extraction

            refined_data = await refine_extraction(raw_text, extracted_data, failed_validations)

            # Update extracted record with refined data
            extracted_record.vendor_name = refined_data.vendor_name
            extracted_record.invoice_number = refined_data.invoice_number
            extracted_record.invoice_date = refined_data.invoice_date
            extracted_record.due_date = refined_data.due_date
            extracted_record.subtotal = refined_data.subtotal
            extracted_record.tax_amount = refined_data.tax_amount
            extracted_record.tax_rate = refined_data.tax_rate
            extracted_record.total_amount = refined_data.total_amount
            extracted_record.line_items = refined_data.line_items
            extracted_record.extraction_confidence = refined_data.extraction_confidence

            # Re-run validation on refined data to see if it passed
            validation_results = await validation_framework.validate(refined_data)

            # Store new validation results (overwriting or appending as "refined" - here we append)
            for result in validation_results:
                refined_validation_record = ValidationResult(
                    id=uuid.uuid4(),
                    invoice_id=invoice.id,
                    rule_name=f"{result.rule_name}_refined",
                    rule_description=f"Refined check: {result.rule_description}",
                    status=ValidationStatus(result.status),
                    expected_value=result.expected_value,
                    actual_value=result.actual_value,
                    tolerance=result.tolerance,
                    error_message=result.error_message,
                )
                session.add(refined_validation_record)

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

