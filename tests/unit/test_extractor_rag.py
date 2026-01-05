"""Unit tests for LlamaIndex RAG-based extraction."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from brain.extractor import extract_invoice_data
from brain.schemas import ExtractedDataSchema


@pytest.mark.asyncio
async def test_extract_invoice_data_basic():
    """Test basic extraction with mocked LlamaIndex components."""
    raw_text = "Invoice from Acme Corp. Number: INV-123. Total: $100.00"
    
    # Mocking the program call and agent
    mock_extracted = ExtractedDataSchema(
        vendor_name="Acme Corp",
        invoice_number="INV-123",
        total_amount=Decimal("100.00"),
        extraction_confidence=Decimal("0.95")
    )
    
    with patch("brain.extractor.OpenAI"), \
         patch("brain.extractor.VectorStoreIndex"), \
         patch("brain.extractor.ReActAgent") as mock_agent_cls, \
         patch("brain.extractor.LLMTextCompletionProgram") as mock_program_cls:
        
        # Mock Agent
        mock_agent = MagicMock()
        mock_agent.chat.return_value = MagicMock(text="Mocked agent analysis")
        mock_agent_cls.from_tools.return_value = mock_agent
        
        # Mock Program
        mock_program = MagicMock()
        mock_program.return_value = mock_extracted
        mock_program_cls.from_defaults.return_value = mock_program
        
        result = await extract_invoice_data(raw_text)
        
        assert result.vendor_name == "Acme Corp"
        assert result.invoice_number == "INV-123"
        assert result.total_amount == Decimal("100.00")
        assert result.raw_text == raw_text


@pytest.mark.asyncio
async def test_extract_invoice_data_empty():
    """Test extraction with empty input."""
    result = await extract_invoice_data("")
    assert result.extraction_confidence == 0.0
    assert result.raw_text == ""
