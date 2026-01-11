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
            from openai import AsyncOpenAI

            self.llm_client = AsyncOpenAI(
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
            
            # Check for ambiguous queries
            if intent.intent_type == QueryHandler.AMBIGUOUS:
                return self._handle_ambiguous_query(message, language)

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
            # Track if we hit the result limit
            has_more = len(invoice_ids) >= settings.CHATBOT_MAX_RESULTS
            assistant_msg = ChatMessage(
                message_id=uuid4(),
                role="assistant",
                content=response,
                timestamp=datetime.utcnow(),
                metadata={
                    "invoice_ids": [UUID(inv["id"]) for inv in invoices_data],
                    "invoice_count": len(invoices_data),
                    "has_more": has_more,
                    "total_found": len(invoice_ids) if has_more else len(invoices_data),
                },
            )
            session.add_message(assistant_msg)
            
            # Add has_more indicator to response if needed
            if has_more and len(invoices_data) > 0:
                if language == "zh":
                    response += f"\n\n[注：找到超过{settings.CHATBOT_MAX_RESULTS}个结果，仅显示前{settings.CHATBOT_MAX_RESULTS}个。请尝试更具体的查询。]"
                else:
                    response += f"\n\n[Note: Found more than {settings.CHATBOT_MAX_RESULTS} results. Showing first {settings.CHATBOT_MAX_RESULTS}. Try a more specific query.]"

            return response

        except Exception as e:
            error_str = str(e)
            logger.error(
                "Error processing message",
                error=error_str,
                error_type=type(e).__name__,
                message_preview=message[:50],
                exc_info=True,
            )
            
            # Check if it's a database error
            if "database" in error_str.lower() or "connection" in error_str.lower() or "transaction" in error_str.lower():
                try:
                    await self.session.rollback()
                    logger.info("Transaction rolled back after engine error")
                except Exception as rollback_err:
                    logger.error("Failed to rollback transaction", error=str(rollback_err))
                return self._get_error_message(language, error_type="database")
            else:
                return self._get_error_message(language, error_type="generic")

    async def _retrieve_invoices(
        self, query: str, intent: QueryIntent
    ) -> List[UUID]:
        """Retrieve relevant invoice IDs using vector search and filters."""
        invoice_ids: List[UUID] = []

        # For aggregate queries, apply filters directly to database query
        if intent.intent_type == QueryHandler.AGGREGATE_QUERY:
            invoice_ids = await self._query_invoices_with_filters(query, intent)
            logger.info("Aggregate query with filters returned results", count=len(invoice_ids))
            return invoice_ids

        # 1. Check for UUID in intent parameters (most specific)
        if intent.parameters and "uuid" in intent.parameters:
            try:
                invoice_ids = [UUID(intent.parameters["uuid"])]
                logger.info("Found UUID in intent parameters", uuid=intent.parameters["uuid"])
                return invoice_ids
            except ValueError:
                pass

        # 2. Check for filename/invoice_number in intent parameters
        if intent.parameters and "invoice_number" in intent.parameters:
            invoice_number = intent.parameters["invoice_number"]
            # If it's a specific filename like "invoice-14.png"
            if "." in invoice_number:
                stmt = select(Invoice.id).where(Invoice.file_name.ilike(f"%{invoice_number}%"))
                result = await self.session.execute(stmt)
                db_ids = [row[0] for row in result.fetchall()]
                if db_ids:
                    logger.info("Found invoices by filename from parameters", invoice_number=invoice_number, count=len(db_ids))
                    return db_ids[: settings.CHATBOT_MAX_RESULTS]

        # 3. For other queries, try vector search (semantic)
        try:
            invoice_ids = await self.vector_retriever.search_similar(
                query_text=query,
                limit=settings.CHATBOT_MAX_RESULTS,
            )
            logger.info("Vector search returned results", count=len(invoice_ids))
        except Exception as e:
            logger.warning("Vector search failed, falling back to database query", error=str(e))

        # 4. If vector search returned no results, try database query as fallback
        if not invoice_ids:
            invoice_ids = await self._query_invoices_from_db(query, intent)

        # 5. Apply additional filters from intent parameters for remaining results
        if intent.parameters and invoice_ids:
            # Filter by invoice number if specified and NOT already handled by filename search
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

            # 1. Search for UUIDs directly in query text
            import re
            uuid_pattern = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
            match = re.search(uuid_pattern, query_lower)
            if match:
                try:
                    uuid_val = UUID(match.group(1))
                    stmt = select(Invoice.id).where(Invoice.id == uuid_val)
                    result = await self.session.execute(stmt)
                    ids = [row[0] for row in result.fetchall()]
                    if ids:
                        logger.info("Found invoice by UUID from query text", uuid=str(uuid_val))
                        return ids
                except ValueError:
                    pass

            # 2. Extract potential filenames (e.g. "invoice-14.png")
            file_pattern = r"\b([a-zA-Z0-9._-]+\.(?:png|jpg|jpeg|pdf|webp|csv|xlsx))\b"
            file_matches = re.findall(file_pattern, query_lower)
            if file_matches:
                file_ids = []
                for fname in file_matches:
                    stmt = select(Invoice.id).where(Invoice.file_name.ilike(f"%{fname}%"))
                    res = await self.session.execute(stmt)
                    file_ids.extend([row[0] for row in res.fetchall()])
                if file_ids:
                    logger.info("Found invoices by filename(s) from query text", filenames=file_matches)
                    return list(dict.fromkeys(file_ids))[:settings.CHATBOT_MAX_RESULTS]

            # 3. Check upload_metadata for subfolder/dataset matches
            if "jimeng" in query_lower:
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
                    return metadata_ids

            # 4. Search in file names with full query
            stmt_file = (
                select(Invoice.id)
                .where(Invoice.file_name.ilike(f"%{query_lower}%"))
                .limit(settings.CHATBOT_MAX_RESULTS)
            )
            result_file = await self.session.execute(stmt_file)
            file_ids = [row[0] for row in result_file.fetchall()]

            # 5. Search in extracted data
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
                pass

            # 6. Keyword fallback: search for individual keywords if still no results
            if not invoice_ids:
                keywords = [k for k in query_lower.split() if len(k) > 3 and k not in ["invoice", "details", "list", "about"]]
                if keywords:
                    logger.info("Trying keyword fallback search", keywords=keywords)
                    keyword_ids = []
                    for kw in keywords:
                        stmt = select(Invoice.id).where(Invoice.file_name.ilike(f"%{kw}%"))
                        res = await self.session.execute(stmt)
                        keyword_ids.extend([row[0] for row in res.fetchall()])
                    if keyword_ids:
                        return list(dict.fromkeys(keyword_ids))[:settings.CHATBOT_MAX_RESULTS]

            unique_ids = list(dict.fromkeys(invoice_ids))[: settings.CHATBOT_MAX_RESULTS]

            logger.info("Database query returned results", count=len(unique_ids))
            return unique_ids

        except Exception as e:
            error_str = str(e)
            logger.error(
                "Database query failed",
                error=error_str,
                error_type=type(e).__name__,
                query_preview=query[:50],
                exc_info=True,
            )
            # CRITICAL: Rollback after error so subsequent queries can proceed
            try:
                await self.session.rollback()
                logger.info("Transaction rolled back after database query failure")
            except Exception as rollback_err:
                logger.error("Failed to rollback transaction", error=str(rollback_err))
            # Return empty list - error handling will be done at higher level
            return []

    async def _query_invoices_with_filters(
        self, query: str, intent: QueryIntent
    ) -> List[UUID]:
        """Query invoices with date range and vendor filters for aggregate queries."""
        try:
            from datetime import datetime, date
            from sqlalchemy import and_, or_

            params = intent.parameters
            stmt = select(Invoice.id).outerjoin(ExtractedData, Invoice.id == ExtractedData.invoice_id)

            conditions = []

            # Vendor filter
            if "vendor_name" in params:
                vendor_name = params["vendor_name"]
                conditions.append(ExtractedData.vendor_name.ilike(f"%{vendor_name}%"))

            # Date range filters
            if "year" in params:
                year = params["year"]
                if "month" in params:
                    month = params["month"]
                    # Filter by year and month
                    conditions.append(
                        func.extract("year", ExtractedData.invoice_date) == year
                    )
                    conditions.append(
                        func.extract("month", ExtractedData.invoice_date) == month
                    )
                else:
                    # Filter by year only
                    conditions.append(
                        func.extract("year", ExtractedData.invoice_date) == year
                    )

            # Apply conditions
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Limit results
            stmt = stmt.limit(settings.CHATBOT_MAX_RESULTS)

            result = await self.session.execute(stmt)
            invoice_ids = [row[0] for row in result.fetchall()]

            logger.info("Filtered query returned results", count=len(invoice_ids), filters=params)
            return invoice_ids

        except Exception as e:
            logger.error("Filtered query failed", error=str(e), exc_info=True)
            # Rollback before fallback query
            try:
                await self.session.rollback()
                logger.info("Transaction rolled back after filtered query failure")
            except Exception as rollback_err:
                logger.error("Failed to rollback transaction", error=str(rollback_err))
            # Fallback to basic query
            return await self._query_invoices_from_db(query, intent)

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
                "storage_path": invoice.storage_path,
                "processing_status": (
                    invoice.processing_status.value 
                    if hasattr(invoice.processing_status, "value") 
                    else str(invoice.processing_status)
                ),
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
            # Build context from conversation history (use full context window)
            # Exclude the current user message which will be added separately
            context_messages = []
            for msg in session.messages[:-1]:  # All messages except the last one (current user message)
                context_messages.append(
                    {"role": msg.role, "content": msg.content}
                )

            # Enhance message with follow-up resolution if needed
            enhanced_message = self._resolve_followup_references(message, session)

            # Build system prompt
            system_prompt = self._build_system_prompt(intent, language, session)

            # Build user prompt with invoice data
            user_prompt = self._build_user_prompt(enhanced_message, invoices_data, intent)

            # Call LLM with full conversation context
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            # Add conversation history (context window already managed by session)
            messages.extend(context_messages)
            # Add current user prompt
            messages.append({"role": "user", "content": user_prompt})

            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=settings.DEEPSEEK_TEMPERATURE,
            )

            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e)
            logger.error(
                "LLM generation failed",
                error=error_str,
                error_type=type(e).__name__,
                message_preview=message[:50],
            )
            
            # Check for specific error types
            if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                return self._get_error_message(language, error_type="timeout")
            elif "rate limit" in error_str.lower() or "429" in error_str:
                return self._get_error_message(language, error_type="rate_limit")
            elif "authentication" in error_str.lower() or "401" in error_str or "403" in error_str:
                return self._get_error_message(language, error_type="auth")
            else:
                return self._generate_simple_response(intent, invoices_data)

    def _build_system_prompt(
        self, intent: QueryIntent, language: str, session: ConversationSession
    ) -> str:
        """Build system prompt for LLM with context awareness."""
        base_prompt_zh = (
            "你是一个专业的发票查询助手。请用中文回答用户关于发票的问题。"
            "你可以参考之前的对话历史来理解用户的后续问题。"
            "当用户使用'那些'、'它们'、'它'等代词时，请根据上下文理解用户指的是什么。"
        )
        base_prompt_en = (
            "You are a helpful invoice query assistant. "
            "Answer questions about invoices clearly and concisely. "
            "Use the provided invoice data to answer accurately. "
            "You can reference previous conversation history to understand follow-up questions. "
            "When users use pronouns like 'those', 'them', 'it', interpret them based on the conversation context."
        )

        if language == "zh":
            return base_prompt_zh
        else:
            return base_prompt_en

    def _handle_ambiguous_query(self, message: str, language: str) -> str:
        """Handle ambiguous queries by asking for clarification."""
        if language == "zh":
            return (
                "您的问题可能有多种理解方式。请提供更多细节，例如：\n"
                "- 您想查找特定发票吗？请提供发票号或供应商名称。\n"
                "- 您想进行统计分析吗？请说明您需要什么类型的统计（总数、平均值等）。\n"
                "- 您想查看特定时间段的发票吗？请提供日期范围。"
            )
        else:
            return (
                "Your question could be interpreted in multiple ways. Please provide more details, such as:\n"
                "- Are you looking for a specific invoice? Please provide an invoice number or vendor name.\n"
                "- Do you want statistical analysis? Please specify what type (total, average, etc.).\n"
                "- Do you want to see invoices from a specific time period? Please provide a date range."
            )

    def _resolve_followup_references(
        self, message: str, session: ConversationSession
    ) -> str:
        """
        Resolve follow-up question references to previous conversation.

        This enhances the message by adding context when pronouns or references
        are detected that might refer to previous answers.
        """
        message_lower = message.lower()

        # Check for common follow-up patterns
        followup_indicators = [
            "those",
            "them",
            "it",
            "that",
            "this",
            "which",
            "what about",
            "how about",
            "and",
            "also",
        ]

        # If message contains follow-up indicators and has conversation history
        if any(indicator in message_lower for indicator in followup_indicators) and len(
            session.messages
        ) > 1:
            # Look for the last assistant message to get context
            last_assistant_msg = None
            for msg in reversed(session.messages[:-1]):  # Exclude current message
                if msg.role == "assistant":
                    last_assistant_msg = msg
                    break

            if last_assistant_msg:
                # Enhance message with context hint
                # The LLM will use the conversation history, but we can add a hint
                enhanced = f"{message}\n\n[Note: This is a follow-up question. Previous context: {last_assistant_msg.content[:200]}...]"
                logger.info("Resolved follow-up reference", original=message[:50])
                return enhanced

        return message

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

            # Add summary for aggregate queries with calculated values
            if intent.intent_type == QueryHandler.AGGREGATE_QUERY:
                agg_type = intent.parameters.get("aggregation_type", "sum")
                agg_result = self._calculate_aggregate(invoices_data, agg_type)
                
                if invoices_with_amounts > 0:
                    prompt += f"\nSummary: Found {len(invoices_data)} invoice(s). "
                    if agg_type == "sum":
                        prompt += f"Total amount: {total_amount:.2f} {currency}"
                    elif agg_type == "count":
                        prompt += f"Count: {len(invoices_data)} invoices"
                    elif agg_type == "average":
                        avg = total_amount / invoices_with_amounts if invoices_with_amounts > 0 else 0
                        prompt += f"Average amount: {avg:.2f} {currency} (from {invoices_with_amounts} invoices)"
                    elif agg_type == "max":
                        prompt += f"Maximum amount: {agg_result:.2f} {currency}"
                    elif agg_type == "min":
                        prompt += f"Minimum amount: {agg_result:.2f} {currency}"
                else:
                    prompt += f"\nSummary: Found {len(invoices_data)} invoice(s), but amounts have not been extracted yet."

        if intent.intent_type == QueryHandler.AGGREGATE_QUERY:
            if invoices_data:
                agg_type = intent.parameters.get("aggregation_type", "sum")
                agg_result = self._calculate_aggregate(invoices_data, agg_type)
                currency = invoices_data[0].get("currency", "USD") if invoices_data else "USD"
                
                prompt += f"\n\nCalculated {agg_type}: {agg_result}"
                if agg_type in ["sum", "average", "max", "min"]:
                    prompt += f" {currency}"
                prompt += f" (from {len(invoices_data)} invoice(s)). "
                prompt += "Please provide a clear, natural language answer using this calculation."
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

        if intent.intent_type == QueryHandler.AGGREGATE_QUERY:
            agg_type = intent.parameters.get("aggregation_type", "count")
            agg_result = self._calculate_aggregate(invoices_data, agg_type)
            currency = invoices_data[0].get("currency", "USD") if invoices_data else "USD"
            
            if agg_type == "count":
                return f"I found {len(invoices_data)} invoice(s)."
            elif agg_type == "sum":
                return f"Total amount: {agg_result:.2f} {currency}"
            elif agg_type == "average":
                invoices_with_amounts = sum(1 for inv in invoices_data if inv.get("total_amount", 0) or 0)
                if invoices_with_amounts > 0:
                    return f"Average amount: {agg_result:.2f} {currency} (from {invoices_with_amounts} invoices)"
                else:
                    return f"I found {len(invoices_data)} invoice(s), but amounts have not been extracted yet."
            elif agg_type == "max":
                return f"Maximum amount: {agg_result:.2f} {currency}"
            elif agg_type == "min":
                return f"Minimum amount: {agg_result:.2f} {currency}"
            else:
                return f"I found {len(invoices_data)} invoice(s)."

        # Simple list response
        response = f"I found {len(invoices_data)} invoice(s):\n"
        for inv in invoices_data[:5]:
            response += f"- {inv.get('invoice_number', 'N/A')}: {inv.get('vendor_name', 'N/A')}\n"
        if len(invoices_data) > 5:
            response += f"... and {len(invoices_data) - 5} more"
        return response

    def _calculate_aggregate(self, invoices_data: List[dict], agg_type: str) -> float:
        """Calculate aggregate value from invoice data."""
        if not invoices_data:
            return 0.0

        amounts = [inv.get("total_amount", 0) or 0 for inv in invoices_data if inv.get("total_amount")]

        if not amounts:
            return 0.0

        if agg_type == "sum":
            return sum(amounts)
        elif agg_type == "count":
            return len(invoices_data)
        elif agg_type == "average":
            return sum(amounts) / len(amounts) if amounts else 0.0
        elif agg_type == "max":
            return max(amounts)
        elif agg_type == "min":
            return min(amounts)
        else:
            return sum(amounts)

    def _get_error_message(self, language: str, error_type: str = "generic") -> str:
        """Get user-friendly error message."""
        error_messages = {
            "generic": {
                "zh": "抱歉，处理您的请求时出现了问题。请稍后再试。",
                "en": "I'm having trouble processing your request. Please try again in a moment.",
            },
            "timeout": {
                "zh": "请求超时。服务器可能正在处理复杂查询，请稍后再试。",
                "en": "Request timed out. The server may be processing a complex query. Please try again.",
            },
            "rate_limit": {
                "zh": "请求过于频繁，请稍后再试。",
                "en": "Too many requests. Please wait a moment before trying again.",
            },
            "auth": {
                "zh": "认证失败。请检查API密钥配置。",
                "en": "Authentication failed. Please check API key configuration.",
            },
            "database": {
                "zh": "数据库连接失败。请稍后再试。",
                "en": "Database connection failed. Please try again later.",
            },
        }

        messages = error_messages.get(error_type, error_messages["generic"])
        return messages.get(language, messages["en"])

