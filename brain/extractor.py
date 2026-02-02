"""Basic data extraction logic mapping raw text to structured data."""

from typing import Any
from pathlib import Path
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


def _resolve_llm_provider() -> str:
    """Resolve LLM provider based on model name and available keys."""
    model_name = settings.LLM_MODEL.lower() if settings.LLM_MODEL else ""
    if "gemini" in model_name:
        return "gemini"
    if "deepseek" in model_name or settings.DEEPSEEK_API_KEY:
        return "deepseek"
    if settings.OPENAI_API_KEY:
        return "openai"
    if settings.GEMINI_API_KEY:
        return "gemini"
    return "none"


def _resolve_gemini_model() -> str:
    """Resolve Gemini model name from settings."""
    if settings.LLM_MODEL and "gemini" in settings.LLM_MODEL.lower():
        return settings.LLM_MODEL
    return settings.GEMINI_MODEL


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
        import json
        llm_provider = _resolve_llm_provider()

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
            "- vendor_name: MUST extract the seller/vendor name. Look for labels like 'Vendor:', 'Seller:', 'Business Name:', '销售方', 'FUME:', 'PRICE:', or company names in the header. If a line looks like an address but has a name above or beside it, that name is usually the vendor.\n"
            "- Extract all amounts as numbers. Ignore currency symbols or commas.\n"
            "- Ensure dates are in YYYY-MM-DD format. If only month/year or other partial dates, try to infer or set null if ambiguous.\n"
            "- RESOLVE CONFLICTING TOTALS: If the document contains multiple totals (e.g., Subtotal vs Pay Amount), "
            "choose the values that are mathematically consistent (Subtotal + Tax = Total). Use line item sums as a hint if subtotal is messy.\n"
            "- OCR NOISE: The text might contain misread characters (e.g. '0' for 'O', 'I' for '1'). Use context to correct these.\n"
            "- TABULAR DATA: Map line item columns correctly. Description, Quantity, Unit Price, and Amount are common.\n"
        )

        user_content = f"RAW TEXT FROM DOCUMENT:\n---------------------\n{raw_text}\n---------------------\n"
        if metadata:
            # Format metadata nicely for the LLM to use as hints
            file_name = metadata.get("file_name") or (Path(metadata["file_path"]).name if "file_path" in metadata else "N/A")
            user_content += f"\nADDITIONAL METADATA HINTS:\nFilename: {file_name}\n"
            user_content += f"\nHint: If vendor_name is not clear in raw text, use the filename '{file_name}' (strip extension and numbers) as a fallback for vendor_name.\n"

        if llm_provider == "gemini":
            from google import genai
            from google.genai import types

            logger.info("Using Gemini via google-genai client", model=_resolve_gemini_model())
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=_resolve_gemini_model(),
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=settings.GEMINI_TEMPERATURE,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
        else:
            # Initialize direct OpenAI client for better compatibility with DeepSeek
            import openai

            if "deepseek" in settings.LLM_MODEL.lower() or settings.DEEPSEEK_API_KEY:
                logger.info("Using DeepSeek via direct OpenAI client", model=settings.LLM_MODEL)
                client = openai.OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY,
                    base_url="https://api.deepseek.com/v1",
                )
            else:
                logger.info("Using OpenAI via direct client", model=settings.LLM_MODEL)
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            # Execute extraction using standard chat completion
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
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

    try:
        import json
        llm_provider = _resolve_llm_provider()

        system_prompt = (
            "You are an expert invoice processing agent. A previous extraction attempt failed some validation checks.\n"
            "Your task is to re-examine the raw text and the previously extracted (incorrect) data, then provide a corrected version.\n"
            "\n"
            "VALIDATION FAILURES TO FIX:\n"
            f"{error_summary}\n"
            "\n"
            "Return ONLY a valid JSON object following the standard invoice structure."
        )

        user_content = (
            f"PREVIOUS DATA:\n{previous_data.model_dump_json(indent=2)}\n\n"
            f"RAW TEXT FROM DOCUMENT:\n---------------------\n{raw_text}\n---------------------\n"
        )

        if llm_provider == "gemini":
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=_resolve_gemini_model(),
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=settings.GEMINI_TEMPERATURE,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
        else:
            import openai

            if "deepseek" in settings.LLM_MODEL.lower() or settings.DEEPSEEK_API_KEY:
                client = openai.OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY or settings.OPENAI_API_KEY,
                    base_url="https://api.deepseek.com/v1",
                )
            else:
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,  # Lower temperature for refinement
            )

            content = response.choices[0].message.content
        if not content:
            return previous_data

        json_str = content.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)
        refined_data = ExtractedDataSchema(**data)
        refined_data.raw_text = raw_text
        
        # Increase confidence slightly to indicate "refined", but cap at 1.0
        current_conf = previous_data.extraction_confidence or Decimal("0")
        refined_data.extraction_confidence = min(current_conf + Decimal("0.05"), Decimal("1.0"))
        
        logger.info("Extraction refinement successful")
        return refined_data

    except Exception as e:
        logger.error("Extraction refinement failed", error=str(e))
        return previous_data

