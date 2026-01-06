"""Main chatbot engine integrating all components."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.config import settings
from core.logging import get_logger
from core.models import Invoice, ExtractedData, ValidationResult
from brain.chatbot.session_manager import ConversationSession, ChatMessage
from brain.chatbot.vector_retriever import VectorRetriever
from brain.chatbot.query_handler import QueryHandler, QueryIntent

logger = get_logger(__name__)


class ChatbotEngine:
    """Main chatbot engine for processing queries and generating responses."""

    def __init__(self, session: AsyncSession):
        """Initialize chatbot engine."""
        self.session = session
        self.vector_retriever = VectorRetriever(session=session)
        self.query_handler = QueryHandler()

        # Initialize DeepSeek client
        # Note: Using OpenAI-compatible client for DeepSeek
        try:
            from openai import OpenAI

            self.llm_client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1",  # DeepSeek API endpoint
            )
            self.llm_model = settings.DEEPSEEK_MODEL
        except ImportError:
            logger.warning("OpenAI client not available, LLM features disabled")
            self.llm_client = None
            self.llm_model = None

    async def process_message(
        self,
        message: str,
        session: ConversationSession,
        language: str = "en",
    ) -> str:
        """
        Process a user message and generate a response.

        Args:
            message: User's message
            session: Conversation session
            language: Language preference (en/zh)

        Returns:
            Chatbot response
        """
        try:
            # Add user message to session
            user_msg = ChatMessage(
                message_id=uuid4(),
                role="user",
                content=message,
                timestamp=datetime.utcnow(),
            )
            session.add_message(user_msg)

            # Classify intent
            intent = self.query_handler.classify_intent(message)

            # Retrieve relevant invoices
            invoice_ids = await self._retrieve_invoices(message, intent)

            # Get invoice data
            invoices_data = await self._get_invoices_data(invoice_ids)

            # If no invoices found but query asks about count/total,
            # try to get ALL invoices to answer the question
            if not invoices_data and ("how many" in message.lower() or "total" in message.lower() or "count" in message.lower()):
                logger.info("No specific invoices found, trying to get all invoices for aggregate query")
                all_invoices_stmt = (
                    select(Invoice.id)
                    .outerjoin(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                    .limit(settings.CHATBOT_MAX_RESULTS)
                )
                all_result = await self.session.execute(all_invoices_stmt)
                all_ids = [row[0] for row in all_result.fetchall()]
                if all_ids:
                    invoices_data = await self._get_invoices_data(all_ids)
                    logger.info("Retrieved all invoices for aggregate query", count=len(invoices_data))

            # Generate response
            response = await self._generate_response(
                message=message,
                intent=intent,
                invoices_data=invoices_data,
                session=session,
                language=language,
            )

            # Add assistant message to session
            assistant_msg = ChatMessage(
                message_id=uuid4(),
                role="assistant",
                content=response,
                timestamp=datetime.utcnow(),
                metadata={
                    "invoice_ids": [UUID(inv["id"]) for inv in invoices_data],
                    "invoice_count": len(invoices_data),
                    "has_more": len(invoices_data) >= settings.CHATBOT_MAX_RESULTS,
                },
            )
            session.add_message(assistant_msg)

            return response

        except Exception as e:
            logger.error("Error processing message", error=str(e), message=message)
            return self._get_error_message(language)

    async def _retrieve_invoices(
        self, query: str, intent: QueryIntent
    ) -> List[UUID]:
        """Retrieve relevant invoice IDs using vector search and filters."""
        invoice_ids: List[UUID] = []

        # Try vector search first
        try:
            invoice_ids = await self.vector_retriever.search_similar(
                query_text=query,
                limit=settings.CHATBOT_MAX_RESULTS,
            )
            logger.info("Vector search returned results", count=len(invoice_ids))
        except Exception as e:
            logger.warning("Vector search failed, falling back to database query", error=str(e))

        # If vector search returned no results, try database query as fallback
        if not invoice_ids:
            invoice_ids = await self._query_invoices_from_db(query, intent)

        # Apply additional filters from intent parameters
        if intent.parameters and invoice_ids:
            # Filter by invoice number if specified
            if "invoice_number" in intent.parameters:
                invoice_number = intent.parameters["invoice_number"]
                filtered_ids = await self._filter_by_invoice_number(invoice_ids, invoice_number)
                if filtered_ids:
                    invoice_ids = filtered_ids

        return invoice_ids[: settings.CHATBOT_MAX_RESULTS]

    async def _query_invoices_from_db(
        self, query: str, intent: QueryIntent
    ) -> List[UUID]:
        """Fallback: Query invoices directly from database using text search."""
        try:
            query_lower = query.lower()

            # First, check upload_metadata for subfolder/dataset matches (e.g., "jimeng")
            if "jimeng" in query_lower or "dataset" in query_lower:
                # Check for subfolder in upload_metadata using JSONB path extraction
                stmt_metadata = (
                    select(Invoice.id)
                    .where(
                        func.jsonb_extract_path_text(Invoice.upload_metadata, "subfolder").ilike("%jimeng%")
                    )
                    .limit(settings.CHATBOT_MAX_RESULTS)
                )
                result_metadata = await self.session.execute(stmt_metadata)
                metadata_ids = [row[0] for row in result_metadata.fetchall()]

                if metadata_ids:
                    logger.info("Found invoices from metadata search", count=len(metadata_ids))
                    return metadata_ids

            # Query invoices - search in file names first (most reliable when extracted data is missing)
            stmt_file = (
                select(Invoice.id)
                .where(Invoice.file_name.ilike(f"%{query_lower}%"))
                .limit(settings.CHATBOT_MAX_RESULTS)
            )
            result_file = await self.session.execute(stmt_file)
            file_ids = [row[0] for row in result_file.fetchall()]

            # Also try searching in extracted data (if available)
            invoice_ids = list(file_ids)
            try:
                stmt_extracted = (
                    select(Invoice.id)
                    .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                    .where(
                        (ExtractedData.vendor_name.ilike(f"%{query_lower}%"))
                        | (ExtractedData.invoice_number.ilike(f"%{query_lower}%"))
                    )
                    .limit(settings.CHATBOT_MAX_RESULTS)
                )
                result_extracted = await self.session.execute(stmt_extracted)
                extracted_ids = [row[0] for row in result_extracted.fetchall()]
                invoice_ids.extend(extracted_ids)
            except Exception:
                # If extracted data search fails, just use file name results
                pass

            # Remove duplicates and limit
            unique_ids = list(dict.fromkeys(invoice_ids))[: settings.CHATBOT_MAX_RESULTS]

            logger.info("Database query returned results", count=len(unique_ids))
            return unique_ids

        except Exception as e:
            logger.error("Database query failed", error=str(e), exc_info=True)
            return []

    async def _filter_by_invoice_number(
        self, invoice_ids: List[UUID], invoice_number: str
    ) -> List[UUID]:
        """Filter invoice IDs by invoice number."""
        try:
            stmt = (
                select(Invoice.id)
                .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                .where(
                    Invoice.id.in_(invoice_ids),
                    ExtractedData.invoice_number.ilike(f"%{invoice_number}%"),
                )
            )
            result = await self.session.execute(stmt)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error("Invoice number filter failed", error=str(e))
            return invoice_ids

    async def _get_invoices_data(self, invoice_ids: List[UUID]) -> List[dict]:
        """Get invoice data for the given invoice IDs."""
        if not invoice_ids:
            return []

        # Query invoices with extracted data (outer join in case extracted_data is missing)
        stmt = (
            select(Invoice, ExtractedData)
            .outerjoin(ExtractedData, Invoice.id == ExtractedData.invoice_id)
            .where(Invoice.id.in_(invoice_ids))
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        invoices_data = []
        for row in rows:
            invoice = row[0]
            extracted_data = row[1] if len(row) > 1 else None

            # Build invoice dict with available data
            invoice_dict = {
                "id": str(invoice.id),
                "file_name": invoice.file_name,
                "file_path": invoice.file_path,
                "processing_status": invoice.processing_status.value,
                "invoice_number": extracted_data.invoice_number if extracted_data else None,
                "vendor_name": extracted_data.vendor_name if extracted_data else None,
                "invoice_date": (
                    extracted_data.invoice_date.isoformat()
                    if extracted_data and extracted_data.invoice_date
                    else None
                ),
                "total_amount": (
                    float(extracted_data.total_amount)
                    if extracted_data and extracted_data.total_amount
                    else None
                ),
                "currency": extracted_data.currency if extracted_data else "USD",
                "line_items": extracted_data.line_items if extracted_data else None,
            }

            # Add upload metadata if available
            if invoice.upload_metadata:
                invoice_dict["upload_metadata"] = invoice.upload_metadata
                if "subfolder" in invoice.upload_metadata:
                    invoice_dict["subfolder"] = invoice.upload_metadata["subfolder"]

            invoices_data.append(invoice_dict)

        return invoices_data

    async def _generate_response(
        self,
        message: str,
        intent: QueryIntent,
        invoices_data: List[dict],
        session: ConversationSession,
        language: str,
    ) -> str:
        """Generate natural language response using LLM."""
        # Handle general questions that don't need invoice data
        message_lower = message.lower()
        general_phrases = ["who are you", "what are you", "introduce yourself", "what can you do"]
        if any(phrase in message_lower for phrase in general_phrases):
            if language == "zh":
                return (
                    "我是一个发票查询助手，可以帮助您查询和分析发票数据。"
                    "我可以回答关于发票的问题，比如：\n"
                    "- 查找特定发票（通过供应商、发票号等）\n"
                    "- 计算总金额、统计发票数量\n"
                    "- 查询特定数据集（如jimeng文件夹）的发票\n"
                    "- 分析发票的详细信息"
                )
            else:
                return (
                    "I'm an invoice query assistant. I can help you search and analyze invoice data. "
                    "I can answer questions about invoices, such as:\n"
                    "- Finding specific invoices (by vendor, invoice number, etc.)\n"
                    "- Calculating totals and counting invoices\n"
                    "- Querying invoices from specific datasets (like the jimeng folder)\n"
                    "- Analyzing invoice details"
                )

        if not self.llm_client:
            # Fallback to simple response
            return self._generate_simple_response(intent, invoices_data)

        try:
            # Build context from conversation history
            context_messages = []
            for msg in session.messages[-5:]:  # Last 5 messages for context
                context_messages.append(
                    {"role": msg.role, "content": msg.content}
                )

            # Build system prompt
            system_prompt = self._build_system_prompt(intent, language)

            # Build user prompt with invoice data
            user_prompt = self._build_user_prompt(message, invoices_data, intent)

            # Call LLM
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *context_messages,
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.DEEPSEEK_TEMPERATURE,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            return self._generate_simple_response(intent, invoices_data)

    def _build_system_prompt(self, intent: QueryIntent, language: str) -> str:
        """Build system prompt for LLM."""
        if language == "zh":
            return "你是一个专业的发票查询助手。请用中文回答用户关于发票的问题。"
        else:
            return (
                "You are a helpful invoice query assistant. "
                "Answer questions about invoices clearly and concisely. "
                "Use the provided invoice data to answer accurately."
            )

    def _build_user_prompt(
        self, message: str, invoices_data: List[dict], intent: QueryIntent
    ) -> str:
        """Build user prompt with invoice data."""
        prompt = f"User question: {message}\n\n"

        if not invoices_data:
            prompt += "No invoices found matching the query. "
            prompt += "However, you can still provide a helpful response. "
            prompt += "If the user asked about dataset 'jimeng' or specific folders, "
            prompt += "you can explain that you searched but found no matching invoices, "
            prompt += "or suggest they check if invoices have been processed."
        else:
            prompt += f"Found {len(invoices_data)} invoice(s):\n\n"
            total_amount = 0.0
            currency = "USD"
            invoices_with_amounts = 0

            for inv in invoices_data[:10]:  # Limit to first 10 for prompt
                inv_total = inv.get('total_amount', 0) or 0
                if inv_total > 0:
                    total_amount += inv_total
                    invoices_with_amounts += 1
                if inv.get('currency') and inv.get('currency') != 'USD':
                    currency = inv.get('currency')

                # Build invoice description
                inv_desc = f"- File: {inv.get('file_name', 'N/A')}"
                if inv.get('invoice_number'):
                    inv_desc += f", Invoice #: {inv.get('invoice_number')}"
                if inv.get('vendor_name'):
                    inv_desc += f", Vendor: {inv.get('vendor_name')}"
                if inv.get('subfolder'):
                    inv_desc += f", Folder: {inv.get('subfolder')}"
                if inv_total > 0:
                    inv_desc += f", Total: {inv_total} {inv.get('currency', 'USD')}"
                else:
                    inv_desc += " (amount not extracted yet)"
                prompt += inv_desc + "\n"

            # Add summary for aggregate queries
            if intent.intent_type == QueryIntent.AGGREGATE_QUERY:
                if invoices_with_amounts > 0:
                    prompt += f"\nSummary: Found {len(invoices_data)} invoice(s). "
                    prompt += f"Total amount from {invoices_with_amounts} invoices with amounts: {total_amount:.2f} {currency}"
                else:
                    prompt += f"\nSummary: Found {len(invoices_data)} invoice(s), but amounts have not been extracted yet."

        if intent.intent_type == QueryIntent.AGGREGATE_QUERY:
            if invoices_data:
                agg_type = intent.parameters.get("aggregation_type", "sum")
                prompt += f"\n\nPlease calculate the requested {agg_type} from the invoice data above and provide a clear answer."
            else:
                prompt += "\nThe user asked for an aggregate calculation, but no invoices were found. Explain this clearly."

        prompt += "\n\nProvide a clear, natural language response to the user's question. Be helpful and informative."

        return prompt

    def _generate_simple_response(
        self, intent: QueryIntent, invoices_data: List[dict]
    ) -> str:
        """Generate simple response without LLM (fallback)."""
        if not invoices_data:
            return (
                "I couldn't find any invoices matching your query. "
                "This might mean:\n"
                "- The invoices haven't been processed yet\n"
                "- The search terms don't match any invoice data\n"
                "- Try rephrasing your question or checking if invoices are in the system"
            )

        if intent.intent_type == QueryIntent.AGGREGATE_QUERY:
            agg_type = intent.parameters.get("aggregation_type", "count")
            if agg_type == "count":
                return f"I found {len(invoices_data)} invoice(s)."
            elif agg_type == "sum":
                total = sum(
                    inv.get("total_amount", 0) or 0 for inv in invoices_data
                )
                currency = invoices_data[0].get("currency", "USD") if invoices_data else "USD"
                return f"Total amount: {total:.2f} {currency}"
            else:
                return f"I found {len(invoices_data)} invoice(s)."

        # Simple list response
        response = f"I found {len(invoices_data)} invoice(s):\n"
        for inv in invoices_data[:5]:
            response += f"- {inv.get('invoice_number', 'N/A')}: {inv.get('vendor_name', 'N/A')}\n"
        if len(invoices_data) > 5:
            response += f"... and {len(invoices_data) - 5} more"
        return response

    def _get_error_message(self, language: str) -> str:
        """Get user-friendly error message."""
        if language == "zh":
            return "抱歉，处理您的请求时出现了问题。请稍后再试。"
        else:
            return "I'm having trouble processing your request. Please try again in a moment."

