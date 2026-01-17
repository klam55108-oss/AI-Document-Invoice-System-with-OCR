"""Job handlers for asynchronous processing."""

from pgqueuer.models import Job
from core.logging import get_logger
from core.queue import get_pgq
from core.database import get_session_factory
from ingestion.orchestrator import process_invoice_file
from pathlib import Path
import json
import uuid

logger = get_logger(__name__)

async def test_job_handler(job: Job) -> None:
    """A sample job handler for verification."""
    logger.info("Executing test job", job_id=job.id, payload=job.payload)
    # Simulate some work
    import asyncio
    await asyncio.sleep(1)
    logger.info("Test job completed", job_id=job.id)

async def process_invoice_handler(job: Job) -> None:
    """Job handler for processing an invoice file."""
    logger.info("Executing invoice processing job", job_id=job.id)
    
    try:
        if isinstance(job.payload, bytes):
            payload = json.loads(job.payload.decode("utf-8"))
        else:
            payload = job.payload
            
        file_path = Path(payload["file_path"])
        data_dir = Path(payload.get("data_dir", "data"))
        force_reprocess = payload.get("force_reprocess", False)
        category = payload.get("category")
        group = payload.get("group")
        invoice_job_id = payload.get("job_id")
        ocr_provider = payload.get("ocr_provider")
        if invoice_job_id:
            invoice_job_id = uuid.UUID(invoice_job_id)
            
        session_factory = get_session_factory()
        async with session_factory() as session:
            invoice = await process_invoice_file(
                file_path=file_path,
                data_dir=data_dir,
                session=session,
                force_reprocess=force_reprocess,
                category=category,
                group=group,
                job_id=invoice_job_id,
                ocr_provider=ocr_provider,
            )
            await session.commit()
            logger.info("Invoice processing job completed", job_id=job.id, invoice_id=str(invoice.id), status=invoice.processing_status.value)
            
    except Exception as e:
        logger.error("Invoice processing job failed", job_id=job.id, error=str(e), exc_info=True)
        # We don't re-raise here to avoid hitting pgqueuer retries immediately 
        # unless we want pgqueuer to handle retries. 
        # The invoice status is already updated to FAILED by process_invoice_file.

async def register_handlers() -> None:
    """Register all job handlers with the queue."""
    pgq = await get_pgq()
    
    @pgq.entrypoint("test_job")
    async def handle_test_job(job: Job) -> None:
        await test_job_handler(job)
        
    @pgq.entrypoint("process_invoice")
    async def handle_process_invoice(job: Job) -> None:
        await process_invoice_handler(job)
    
    logger.info("Job handlers registered")
