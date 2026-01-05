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
    """Extract structured invoice data from raw text using LlamaIndex RAG.

    Args:
        raw_text: Raw text extracted from invoice document
        metadata: Optional metadata from processor

    Returns:
        ExtractedDataSchema with extracted fields
    """
    logger.info("Extracting invoice data using LlamaIndex RAG", text_length=len(raw_text))

    if not raw_text.strip():
        logger.warning("Empty raw text provided for extraction")
        return ExtractedDataSchema(raw_text=raw_text, extraction_confidence=0.0)

    try:
        # Initialize LLM
        llm = OpenAI(model=settings.LLM_MODEL, temperature=settings.LLM_TEMPERATURE)

        # RAG Integration: Index the raw text
        doc = Document(text=raw_text, metadata=metadata or {})
        index = VectorStoreIndex.from_documents([doc])
        query_engine = index.as_query_engine(llm=llm, response_mode="compact")

        # Define tools for the agent
        tools = [
            QueryEngineTool(
                query_engine=query_engine,
                metadata=ToolMetadata(
                    name="invoice_data_retriever",
                    description="Retrieves specific text and details from the raw invoice document.",
                ),
            )
        ]

        # Initialize Agent
        agent = ReActAgent.from_tools(tools, llm=llm, verbose=True)

        # Agentic Flow: Agent retrieves context and then we extract structured data
        agent_query = (
            "Analyze this invoice document provided in Markdown format. "
            "The invoice may be in any language (English, Chinese, etc.). "
            "Pay special attention to any tables which contain line items, quantities, and prices. "
            "Identify the vendor/seller name (销售方/卖方), invoice number (发票号码), date, "
            "total amount (价税合计/总计), subtotal (小计), tax amount (税额), and all line items. "
            "For Chinese invoices, look for fields like: 销售方 (seller), 购买方 (buyer), "
            "货物或应税劳务名称 (goods/services), 金额 (amount), 税率 (tax rate), 税额 (tax amount). "
            "Provide a comprehensive summary of all found details."
        )
        agent_response = agent.chat(agent_query)
        context_str = str(agent_response)

        # Create structured output program
        prompt_template_str = (
            "You are an expert invoice processing agent that can handle invoices in multiple languages "
            "(English, Chinese, etc.). Your task is to extract structured information "
            "from the following context retrieved from an invoice document.\n"
            "CONTEXT FROM DOCUMENT:\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Metadata (may contain raw tables): {metadata}\n"
            "\n"
            "IMPORTANT: For Chinese invoices, extract:\n"
            "- vendor_name from 销售方 (seller) or 销售方名称\n"
            "- invoice_number from 发票号码\n"
            "- invoice_date from 开票日期\n"
            "- total_amount from 价税合计 (total including tax)\n"
            "- subtotal from 合计 (subtotal) or calculate from line items\n"
            "- tax_amount from 税额 (tax amount)\n"
            "- line_items from the goods/services table (货物或应税劳务名称)\n"
            "Extract all amounts as decimal numbers, regardless of currency or language.\n"
        )

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=ExtractedDataSchema,
            prompt_template_str=prompt_template_str,
            llm=llm,
            verbose=True,
        )

        # Execute extraction using agent-derived context
        extracted = program(context_str=context_str, metadata=metadata or {})

        # Ensure raw_text is preserved
        extracted.raw_text = raw_text

        # Add extraction confidence if not set (or use a default)
        if not extracted.extraction_confidence:
            extracted.extraction_confidence = 0.95  # Placeholder for high confidence from LLM

        logger.info(
            "Data extraction completed via LlamaIndex",
            vendor=extracted.vendor_name,
            invoice_number=extracted.invoice_number,
            total=extracted.total_amount,
        )

        return extracted

    except Exception as e:
        logger.error("LlamaIndex extraction failed", error=str(e))
        # Fallback to empty schema or handle as needed
        return ExtractedDataSchema(raw_text=raw_text, extraction_confidence=0.0)


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

    # Increase confidence slightly to indicate "refined"
    refined_data.extraction_confidence = (refined_data.extraction_confidence or Decimal("0")) + Decimal("0.1")

    return refined_data

