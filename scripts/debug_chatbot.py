#!/usr/bin/env python3
"""Diagnose chatbot data and test query processing."""

import asyncio
import os
import sys
import json
from datetime import datetime, UTC
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func, text

# Add project root to path
sys.path.append(os.getcwd())

from core.models import Invoice, ExtractedData
from brain.chatbot.engine import ChatbotEngine
from brain.chatbot.session_manager import ConversationSession
from core.config import settings

load_dotenv()

async def debug_chatbot(test_query: str = None):
    """Diagnose data and optionally test a query."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print(f"\n{'='*20} CHATBOT DATA DIAGNOSIS {'='*20}")
            
            # 1. Check total invoices
            stmt = select(func.count(Invoice.id))
            result = await session.execute(stmt)
            total_invoices = result.scalar()
            print(f"📊 Total invoices:        {total_invoices}")

            # 2. Check invoices with extracted data
            stmt = select(func.count(ExtractedData.id))
            result = await session.execute(stmt)
            extracted_count = result.scalar()
            print(f"📄 With extracted data:  {extracted_count}")

            # 3. Check for embeddings
            try:
                stmt = text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoice_embeddings'")
                result = await session.execute(stmt)
                table_exists = result.scalar() > 0
                if table_exists:
                    stmt = text("SELECT COUNT(*) FROM invoice_embeddings")
                    result = await session.execute(stmt)
                    print(f"🔢 Vector embeddings:     {result.scalar()} (✅ Available)")
                else:
                    print(f"🔢 Vector embeddings:     ❌ Missing (Using database fallback)")
            except:
                print(f"🔢 Vector embeddings:     ❌ Error checking table")

            if test_query:
                print(f"\n{'='*20} TESTING QUERY {'='*20}")
                print(f"Query: \"{test_query}\"")
                
                chatbot = ChatbotEngine(session)
                now = datetime.now(UTC)
                chat_session = ConversationSession(
                    session_id=uuid4(),
                    created_at=now,
                    last_activity=now
                )
                
                start_time = datetime.now()
                try:
                    response = await chatbot.process_message(test_query, chat_session)
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    print("-" * 40)
                    print(f"Bot: {response}")
                    print("-" * 40)
                    print(f"Latency: {duration:.2f}s")
                except Exception as e:
                    print(f"❌ Chatbot failed: {e}")
                    import traceback
                    traceback.print_exc()

    finally:
        await engine.dispose()

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(debug_chatbot(query))
