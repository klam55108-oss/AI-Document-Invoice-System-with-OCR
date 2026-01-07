"""Vector retrieval for invoice similarity search using pgvector."""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import numpy as np
# Deferred import for sentence_transformers to handle missing dependency gracefully

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class VectorRetriever:
    """Retrieves invoices using vector similarity search."""

    def __init__(self, model_name: str | None = None, session: AsyncSession | None = None):
        """Initialize vector retriever with embedding model."""
        self.model_name = model_name or settings.EMBED_MODEL
        self.model: SentenceTransformer | None = None
        self.session = session
        self._model_loaded = False

    def _load_model(self) -> None:
        """Lazy load the embedding model."""
        if not self._model_loaded:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading embedding model", model=self.model_name)
                self.model = SentenceTransformer(self.model_name)
                self._model_loaded = True
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. Vector search will be disabled.",
                    model=self.model_name
                )
                self._model_loaded = True # Mark as loaded (but None) to prevent repeated attempts

    async def search_similar(
        self,
        query_text: str,
        limit: int | None = None,
        threshold: float = 0.7,
        session: AsyncSession | None = None,
    ) -> List[UUID]:
        """
        Search for similar invoices using vector similarity.

        Args:
            query_text: User's natural language query
            limit: Maximum number of results (defaults to CHATBOT_MAX_RESULTS)
            threshold: Similarity threshold (0.0-1.0)
            session: Database session (uses self.session if not provided)

        Returns:
            List of invoice UUIDs ordered by similarity
        """
        if session is None:
            session = self.session
        if session is None:
            raise ValueError("Database session required")

        if limit is None:
            limit = settings.CHATBOT_MAX_RESULTS

        # Load model if needed
        self._load_model()
        if self.model is None:
            logger.info("Vector search unavailable (model not loaded), skipping")
            return []

        try:
            # Embed query
            query_embedding = self.model.encode(query_text, convert_to_numpy=True)
            embedding_dim = len(query_embedding)

            # Convert to PostgreSQL vector format
            # pgvector expects format: [0.1,0.2,0.3,...]
            query_vector_str = "[" + ",".join(map(str, query_embedding.tolist())) + "]"

            # Vector similarity search in pgvector
            # Using cosine distance (<=> operator) - lower is more similar
            # Note: This assumes invoice_embeddings table exists with structure:
            #   invoice_id UUID, embedding vector(N)
            # If table doesn't exist, fall back to simple text search
            query = text("""
                SELECT invoice_id, embedding <=> :query_vector::vector AS distance
                FROM invoice_embeddings
                WHERE embedding <=> :query_vector::vector < :threshold
                ORDER BY distance
                LIMIT :limit
            """)

            result = await session.execute(
                query,
                {
                    "query_vector": query_vector_str,
                    "threshold": threshold,
                    "limit": limit,
                },
            )

            rows = result.fetchall()
            invoice_ids = [UUID(str(row[0])) for row in rows]

            logger.info(
                "Vector search completed",
                query_length=len(query_text),
                results_count=len(invoice_ids),
            )

            return invoice_ids

        except Exception as e:
            error_str = str(e)
            # Check if table doesn't exist
            if "does not exist" in error_str.lower() or "relation" in error_str.lower():
                logger.warning(
                    "invoice_embeddings table not found. Vector search unavailable. "
                    "Please ensure embeddings are stored in pgvector."
                )
            else:
                logger.error("Vector search failed", error=error_str, query=query_text)
            
            # CRITICAL: Rollback to clear the "aborted transaction" state 
            # so subsequent database queries in the same session can proceed.
            try:
                await session.rollback()
                logger.info("Transaction rolled back after vector search failure")
            except Exception as rollback_err:
                logger.error("Failed to rollback transaction", error=str(rollback_err))
                
            # Fallback: return empty list
            return []

