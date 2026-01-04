"""Basic data extraction logic mapping raw text to structured data."""

import re
from decimal import Decimal
from typing import Any

from brain.schemas import ExtractedDataSchema, LineItem
from core.logging import get_logger

logger = get_logger(__name__)


async def extract_invoice_data(raw_text: str, metadata: dict[str, Any] | None = None) -> ExtractedDataSchema:
    """Extract structured invoice data from raw text.

    This is a basic extraction implementation for the scaffold.
    Future versions will use LLM/RAG for more sophisticated extraction.

    Args:
        raw_text: Raw text extracted from invoice document
        metadata: Optional metadata from processor

    Returns:
        ExtractedDataSchema with extracted fields
    """
    logger.info("Extracting invoice data from text", text_length=len(raw_text))

    # Basic pattern matching for common invoice fields
    # This is a simplified implementation for the scaffold

    extracted = ExtractedDataSchema()

    # Extract amounts (look for currency patterns)
    amount_patterns = [
        r"total[:\s]+[\$]?([\d,]+\.?\d*)",
        r"amount[:\s]+[\$]?([\d,]+\.?\d*)",
        r"[\$]([\d,]+\.?\d*)",
    ]

    amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        for match in matches:
            try:
                amount = Decimal(match.replace(",", ""))
                amounts.append(amount)
            except (ValueError, Exception):
                pass

    if amounts:
        # Assume largest amount is total
        extracted.total_amount = max(amounts)

    # Extract dates (basic pattern)
    date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    dates = re.findall(date_pattern, raw_text)
    if dates:
        # Try to parse first date found
        try:
            # This is simplified - real implementation would parse properly
            extracted.invoice_date = None  # Would parse date here
        except Exception:
            pass

    # Extract vendor name (look for common patterns)
    vendor_patterns = [
        r"(?:from|vendor|supplier|bill from)[:\s]+([A-Z][A-Za-z\s&,]+)",
        r"^([A-Z][A-Za-z\s&,]+)\s*(?:invoice|bill)",
    ]

    for pattern in vendor_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            extracted.vendor_name = match.group(1).strip()
            break

    # Extract invoice number
    invoice_num_patterns = [
        r"invoice[#\s:]+([A-Z0-9\-]+)",
        r"inv[#\s:]+([A-Z0-9\-]+)",
        r"#([A-Z0-9\-]+)",
    ]

    for pattern in invoice_num_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            extracted.invoice_number = match.group(1).strip()
            break

    # Store raw text for future RAG indexing
    extracted.raw_text = raw_text

    # Set basic confidence (scaffold: low confidence for pattern matching)
    extracted.extraction_confidence = Decimal("0.3")

    logger.info(
        "Data extraction completed",
        vendor=extracted.vendor_name,
        invoice_number=extracted.invoice_number,
        total=extracted.total_amount,
    )

    return extracted

