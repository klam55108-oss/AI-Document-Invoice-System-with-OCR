"""Job handlers for asynchronous processing."""

from pgqueuer.models import Job
from core.logging import get_logger
from core.queue import get_pgq

logger = get_logger(__name__)

async def test_job_handler(job: Job) -> None:
    """A sample job handler for verification."""
    logger.info("Executing test job", job_id=job.id, payload=job.payload)
    # Simulate some work
    import asyncio
    await asyncio.sleep(1)
    logger.info("Test job completed", job_id=job.id)

async def register_handlers() -> None:
    """Register all job handlers with the queue."""
    pgq = await get_pgq()
    
    @pgq.entrypoint("test_job")
    async def handle_test_job(job: Job) -> None:
        await test_job_handler(job)
    
    logger.info("Job handlers registered")
