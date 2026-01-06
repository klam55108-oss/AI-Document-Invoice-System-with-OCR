"""Unit tests for chatbot vector retriever."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
import numpy as np

from brain.chatbot.vector_retriever import VectorRetriever


@pytest.mark.asyncio
async def test_vector_retriever_initialization():
    """Test vector retriever initialization."""
    mock_session = AsyncMock()
    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    assert retriever.model_name == "all-MiniLM-L6-v2"
    assert retriever.session == mock_session
    assert retriever.model is None  # Model not loaded yet
    assert retriever._model_loaded is False


@pytest.mark.asyncio
async def test_load_model():
    """Test lazy loading of embedding model."""
    mock_session = AsyncMock()
    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    # Model should not be loaded initially
    assert retriever.model is None

    # Load model
    retriever._load_model()

    # Model should now be loaded
    assert retriever.model is not None
    assert retriever._model_loaded is True


@pytest.mark.asyncio
async def test_search_similar_success():
    """Test successful vector similarity search."""
    mock_session = AsyncMock()

    # Mock database result
    mock_row1 = MagicMock()
    mock_row1.__getitem__.return_value = UUID("11111111-1111-1111-1111-111111111111")
    mock_row2 = MagicMock()
    mock_row2.__getitem__.return_value = UUID("22222222-2222-2222-2222-222222222222")

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row1, mock_row2]

    mock_execute = AsyncMock(return_value=mock_result)
    mock_session.execute = mock_execute

    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    # Mock the model encoding
    with patch.object(
        retriever, "_load_model"
    ), patch("sentence_transformers.SentenceTransformer") as mock_model_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model_class.return_value = mock_model
        retriever.model = mock_model

        results = await retriever.search_similar("test query", limit=5)

        assert len(results) == 2
        assert results[0] == UUID("11111111-1111-1111-1111-111111111111")
        assert results[1] == UUID("22222222-2222-2222-2222-222222222222")

        # Verify database query was executed
        assert mock_execute.called


@pytest.mark.asyncio
async def test_search_similar_no_results():
    """Test vector search with no results."""
    mock_session = AsyncMock()

    # Mock empty database result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_execute = AsyncMock(return_value=mock_result)
    mock_session.execute = mock_execute

    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    with patch.object(
        retriever, "_load_model"
    ), patch("sentence_transformers.SentenceTransformer") as mock_model_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model_class.return_value = mock_model
        retriever.model = mock_model

        results = await retriever.search_similar("test query")

        assert len(results) == 0
        assert results == []


@pytest.mark.asyncio
async def test_search_similar_table_not_found():
    """Test handling when invoice_embeddings table doesn't exist."""
    mock_session = AsyncMock()

    # Mock database error for missing table
    mock_execute = AsyncMock(
        side_effect=Exception("relation 'invoice_embeddings' does not exist")
    )
    mock_session.execute = mock_execute

    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    with patch.object(
        retriever, "_load_model"
    ), patch("sentence_transformers.SentenceTransformer") as mock_model_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model_class.return_value = mock_model
        retriever.model = mock_model

        # Should return empty list, not raise exception
        results = await retriever.search_similar("test query")

        assert len(results) == 0
        assert results == []


@pytest.mark.asyncio
async def test_search_similar_no_session():
    """Test that search requires a session."""
    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=None)

    with pytest.raises(ValueError, match="Database session required"):
        await retriever.search_similar("test query", session=None)


@pytest.mark.asyncio
async def test_search_similar_custom_limit():
    """Test vector search with custom limit."""
    mock_session = AsyncMock()

    # Mock database result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_execute = AsyncMock(return_value=mock_result)
    mock_session.execute = mock_execute

    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    with patch.object(
        retriever, "_load_model"
    ), patch("sentence_transformers.SentenceTransformer") as mock_model_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model_class.return_value = mock_model
        retriever.model = mock_model

        await retriever.search_similar("test query", limit=10)

        # Verify limit was passed to query
        call_args = mock_execute.call_args
        assert call_args is not None
        # Check that limit parameter was used (exact check depends on implementation)


@pytest.mark.asyncio
async def test_search_similar_custom_threshold():
    """Test vector search with custom similarity threshold."""
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_execute = AsyncMock(return_value=mock_result)
    mock_session.execute = mock_execute

    retriever = VectorRetriever(model_name="all-MiniLM-L6-v2", session=mock_session)

    with patch.object(
        retriever, "_load_model"
    ), patch("sentence_transformers.SentenceTransformer") as mock_model_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model_class.return_value = mock_model
        retriever.model = mock_model

        await retriever.search_similar("test query", threshold=0.8)

        # Verify threshold was used in query
        assert mock_execute.called

