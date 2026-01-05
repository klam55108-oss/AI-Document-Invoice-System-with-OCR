"""Verification test for pgqueuer job processing with separate connections."""

import asyncio
import os
import uuid
import json
import pytest
from dotenv import load_dotenv
import asyncpg
from pgqueuer import PgQueuer, Queries, AsyncpgDriver
from pgqueuer.models import Job

load_dotenv()

@pytest.mark.asyncio
async def test_enqueue_and_process_job():
    """Verify that a job can be enqueued and processed."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")
    
    db_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # Connect worker and enqueuer separately
    worker_conn = await asyncpg.connect(db_url)
    enqueuer_conn = await asyncpg.connect(db_url)
    
    try:
        # Initialize pgqueuer worker
        pgq = PgQueuer.from_asyncpg_connection(worker_conn)
        
        # Initialize enqueuer queries
        queries = Queries(AsyncpgDriver(enqueuer_conn))
        
        # Track if the job was handled
        job_handled = asyncio.Event()
        received_payload = None

        @pgq.entrypoint("test_verification_job")
        async def handle_verification_job(job: Job) -> None:
            nonlocal received_payload
            if isinstance(job.payload, bytes):
                received_payload = json.loads(job.payload.decode("utf-8"))
            else:
                received_payload = job.payload
            job_handled.set()

        # Start the queue listener in the background
        listener_task = asyncio.create_task(pgq.run())
        
        # Give the listener a moment to start and LISTEN
        await asyncio.sleep(0.5)

        # Enqueue a job
        test_payload = {"test_id": str(uuid.uuid4()), "message": "Verify with separate connections"}
        payload_bytes = json.dumps(test_payload).encode("utf-8")
        await queries.enqueue("test_verification_job", payload_bytes)

        # Wait for the job to be handled (with timeout)
        try:
            await asyncio.wait_for(job_handled.wait(), timeout=5.0)
            print(f"Successfully processed job with payload: {received_payload}")
            assert received_payload == test_payload
        except asyncio.TimeoutError:
            # Check if job is still in DB
            rows = await enqueuer_conn.fetch("SELECT status FROM pgqueuer WHERE entrypoint = 'test_verification_job'")
            print(f"Job statuses in DB: {rows}")
            pytest.fail("Job was not processed within the timeout period")

    finally:
        # Cleanup
        if 'listener_task' in locals():
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
        
        await worker_conn.close()
        await enqueuer_conn.close()

if __name__ == "__main__":
    asyncio.run(test_enqueue_and_process_job())
