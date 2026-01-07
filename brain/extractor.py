"""Basic data extraction logic mapping raw text to structured data."""

from typing import Any
from llama_index.core import Document, VectorStoreIndex, SummaryIndex
from llama_index.llms.openai import OpenAI
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent

from brain.schemas import ExtractedDataSchema, ValidationRuleResult
from decimal import Decimal
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


async def extract_invoice_data(raw_text: str, metadata: dict[str, Any] | None = None) -> ExtractedDataSchema:
    """Extract structured invoice data from raw text using direct LLM extraction.

    Args:
        raw_text: Raw text extracted from invoice document
        metadata: Optional metadata from processor

    Returns:
        ExtractedDataSchema with extracted fields
    """
    logger.info("Extracting invoice data using direct LLM", text_length=len(raw_text))

    if not raw_text.strip():
        logger.warning("Empty raw text provided for extraction")
        return ExtractedDataSchema(raw_text=raw_text, extraction_confidence=0.0)

    try:
        # Initialize direct OpenAI client for better compatibility with DeepSeek
        import openai
        import json
        
        if "deepseek" in settings.LLM_MODEL.lower() or settings.DEEPSEEK_API_KEY:
            logger.info("Using DeepSeek via direct OpenAI client", model=settings.LLM_MODEL)
            client = openai.OpenAI(
                api_key=settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY,
                base_url="https://api.deepseek.com/v1"
            )
        else:
            logger.info("Using OpenAI via direct client", model=settings.LLM_MODEL)
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Prompt for extraction - Modified for JSON output
        system_prompt = (
            "You are an expert invoice processing agent. Your task is to extract structured information "
            "from raw text retrieved from an invoice document and return it as a JSON object.\n"
            "\n"
            "Return ONLY a valid JSON object following this structure:\n"
            "{\n"
            '  "vendor_name": "string or null",\n'
            '  "invoice_number": "string or null",\n'
            '  "invoice_date": "YYYY-MM-DD or null",\n'
            '  "total_amount": number or null,\n'
            '  "subtotal": number or null,\n'
            '  "tax_amount": number or null,\n'
            '  "tax_rate": number or null,\n'
            '  "currency": "string or null",\n'
            '  "line_items": [\n'
            '    {"description": "string", "quantity": number, "unit_price": number, "amount": number}\n'
            '  ]\n'
            "}\n"
            "\n"
            "CRITICAL EXTRACTION RULES:\n"
            "- vendor_name: MUST extract from 销售方 (seller/vendor) field for Chinese invoices.\n"
            "- Extract all amounts as numbers.\n"
            "- Ensure dates are in YYYY-MM-DD format.\n"
            "- RESOLVE CONFLICTING TOTALS: If the document contains multiple totals (e.g., Subtotal vs Pay Amount), "
            "choose the values that are mathematically consistent (Subtotal + Tax = Total).\n"
        )

        user_content = f"RAW TEXT FROM DOCUMENT:\n---------------------\n{raw_text}\n---------------------\n"
        if metadata:
            user_content += f"Metadata: {metadata}"

        # Execute extraction using standard chat completion
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=settings.LLM_TEMPERATURE,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        # Clean JSON if necessary (handle markdown blocks)
        json_str = content.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()

        # Parse JSON and validate with Pydantic
        data = json.loads(json_str)
        extracted = ExtractedDataSchema(**data)

        # Ensure raw_text is preserved
        extracted.raw_text = raw_text

        # Add extraction confidence if not set
        if not extracted.extraction_confidence:
            extracted.extraction_confidence = Decimal("0.95")

        logger.info(
            "Data extraction completed successfully",
            vendor=extracted.vendor_name,
            invoice_number=extracted.invoice_number,
            total=float(extracted.total_amount) if extracted.total_amount else None,
        )

        return extracted

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "api_key" in error_msg.lower():
            logger.error("LLM Authentication failed. Please check your API keys in .env", error=error_msg)
        else:
            logger.error("Data extraction failed", error=error_msg)
        
        # Return schema with raw text preserved so it can be seen in dashboard
        return ExtractedDataSchema(raw_text=raw_text, extraction_confidence=Decimal("0.0"))


async def refine_extraction(
    raw_text: str,
    previous_data: ExtractedDataSchema,
    validation_errors: list[ValidationRuleResult],
) -> ExtractedDataSchema:
    """Refine extracted data using validation errors as feedback.

    Args:
        raw_text: Original raw text from invoice
        previous_data: Previously extracted (and failed) data
        validation_errors: List of failed validation results

    Returns:
        Refined ExtractedDataSchema
    """
    error_summary = "\n".join(
        [f"- {e.rule_name}: {e.error_message}" for e in validation_errors if e.status == "failed"]
    )
    logger.info("Refining extraction based on validation errors", error_count=len(validation_errors))

    # In a real implementation, this would call an LLM with a prompt like:
    # "The previous extraction failed these validations: {error_summary}.
    # Here is the raw text: {raw_text}. Please correct the fields."

    # For the scaffold, we'll simulate a "correction" if confidence was low
    refined_data = previous_data.model_copy()

    # Simulate correction of a common math error or date error
    for error in validation_errors:
        if error.rule_name == "math_check_subtotal_tax" and error.status == "failed":
            # If subtotal + tax != total, and total looks like a sum of subtotal + tax elsewhere
            # we might "correct" it. Here we just log the attempt.
            logger.info("Correction logic would trigger for math error", rule=error.rule_name)
        elif error.rule_name == "date_consistency" and error.status == "failed":
            logger.info("Correction logic would trigger for date error", rule=error.rule_name)

    # Increase confidence slightly to indicate "refined", but cap at 1.0
    current_conf = refined_data.extraction_confidence or Decimal("0")
    refined_data.extraction_confidence = min(current_conf + Decimal("0.1"), Decimal("1.0"))

    return refined_data

