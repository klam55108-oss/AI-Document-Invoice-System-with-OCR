
import asyncio
import os
import uuid
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Import models
import sys
sys.path.append(os.getcwd())
from core.models import Invoice

async def check_job(job_id_str):
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found")
        return

    engine = create_async_engine(database_url)
    async with AsyncSession(engine) as session:
        job_id = uuid.UUID(job_id_str)
        stmt = select(Invoice).where(Invoice.job_id == job_id)
        result = await session.execute(stmt)
        invoices = result.scalars().all()
        
        if not invoices:
            print(f"No invoices found for job_id: {job_id_str}")
            print("Recent invoices:")
            recent_stmt = select(Invoice).order_by(Invoice.created_at.desc()).limit(5)
            recent_result = await session.execute(recent_stmt)
            for inv in recent_result.scalars().all():
                print(f"ID: {inv.id}, Storage: {inv.storage_path}, Job: {inv.job_id}, Created: {inv.created_at}")
            return
            
        for inv in invoices:
            print(f"Invoice ID: {inv.id}")
            print(f"Storage Path: {inv.storage_path}")
            print(f"Category: {inv.category}")
            print(f"Group: {inv.group}")
            print(f"Status: {inv.processing_status}")
            print("-" * 20)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(check_job(sys.argv[1]))
    else:
        print("Please provide job_id")
