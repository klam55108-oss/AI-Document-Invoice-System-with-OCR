import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.models import Invoice, ProcessingStatus

async def check_errors():
    database_url = "postgresql+asyncpg://einvoice:einvoice_dev@localhost:5432/einvoicing"
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)
    
    async with session_factory() as session:
        # Check for failed invoices
        stmt = select(Invoice).where(Invoice.processing_status == ProcessingStatus.FAILED).order_by(Invoice.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        invoices = result.scalars().all()
        
        print(f"Found {len(invoices)} failed invoices in DB:")
        for inv in invoices:
            print(f"- {inv.file_name}: {inv.error_message}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_errors())
