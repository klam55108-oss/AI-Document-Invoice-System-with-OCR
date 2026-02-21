import asyncio
from sqlalchemy import select, func
from core.database import get_session, init_db
from core.config import settings
from core.models import Invoice

async def check_db():
    await init_db(settings.DATABASE_URL)
    async for session in get_session():
        result = await session.execute(select(Invoice.source_dataset, func.count(Invoice.id)).group_by(Invoice.source_dataset))
        counts = result.fetchall()
        print("\nDataset Counts:")
        total = 0
        for dataset, count in counts:
            print(f"  {dataset}: {count}")
            total += count
        print(f"Total: {total}")
        break

if __name__ == "__main__":
    asyncio.run(check_db())
