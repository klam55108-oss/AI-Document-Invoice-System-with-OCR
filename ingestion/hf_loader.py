"""HuggingFace dataset loader entry point."""

import asyncio
from core.database import get_session, init_db
from core.config import settings
from core.logging import get_logger
from ingestion.hf_datasets.pipeline import IngestionPipeline

logger = get_logger(__name__)

async def main():
    """Run the multi-dataset ingestion pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest HuggingFace invoice datasets")
    parser.add_argument("--limit", type=int, default=10, help="Limit per dataset")
    args = parser.parse_args()

    logger.info("Initializing database...")
    await init_db(settings.DATABASE_URL)
    
    try:
        async for session in get_session():
            pipeline = IngestionPipeline(session)
            logger.info(f"Starting ingestion with limit={args.limit} per dataset...")
            await pipeline.run(limit_per_dataset=args.limit)
            break
    finally:
        from core.database import close_db
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
