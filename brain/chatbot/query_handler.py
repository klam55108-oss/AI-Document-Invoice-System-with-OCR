"""Query intent classification and parameter extraction."""

from typing import Dict, Any, Optional
from datetime import date
from decimal import Decimal

from core.logging import get_logger

logger = get_logger(__name__)


class QueryIntent:
    """Represents classified query intent."""

    def __init__(
        self,
        intent_type: str,
        parameters: Dict[str, Any],
        confidence: float = 1.0,
    ):
        """Initialize query intent."""
        self.intent_type = intent_type
        self.parameters = parameters
        self.confidence = confidence


class QueryHandler:
    """Handles query intent classification and parameter extraction."""

    # Intent types
    FIND_INVOICE = "find_invoice"
    AGGREGATE_QUERY = "aggregate_query"
    LIST_INVOICES = "list_invoices"
    GET_DETAILS = "get_details"
    AMBIGUOUS = "ambiguous"

    def __init__(self):
        """Initialize query handler."""
        pass

    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify query intent and extract parameters.

        This is a simple rule-based classifier. In production, this could
        use an LLM for more sophisticated classification.

        Args:
            query: User's natural language query

        Returns:
            QueryIntent with classified intent and extracted parameters
        """
        query_lower = query.lower().strip()

        # Simple keyword-based classification
        # Check for aggregate keywords
        aggregate_keywords = [
            "total",
            "sum",
            "count",
            "average",
            "avg",
            "how many",
            "percentage",
            "most",
            "highest",
            "lowest",
        ]
        if any(keyword in query_lower for keyword in aggregate_keywords):
            return QueryIntent(
                intent_type=self.AGGREGATE_QUERY,
                parameters=self._extract_aggregate_params(query),
                confidence=0.8,
            )

        # Check for list keywords
        list_keywords = ["show", "list", "find all", "get all", "display"]
        if any(keyword in query_lower for keyword in list_keywords):
            return QueryIntent(
                intent_type=self.LIST_INVOICES,
                parameters=self._extract_filter_params(query),
                confidence=0.8,
            )

        # Check for detail keywords
        detail_keywords = ["what", "details", "information", "tell me about"]
        if any(keyword in query_lower for keyword in detail_keywords):
            return QueryIntent(
                intent_type=self.GET_DETAILS,
                parameters=self._extract_filter_params(query),
                confidence=0.7,
            )

        # Default to find_invoice
        return QueryIntent(
            intent_type=self.FIND_INVOICE,
            parameters=self._extract_filter_params(query),
            confidence=0.6,
        )

    def _extract_filter_params(self, query: str) -> Dict[str, Any]:
        """Extract filter parameters from query."""
        params: Dict[str, Any] = {}
        query_lower = query.lower()
        import re

        # Extract vendor name (simple pattern matching)
        # Look for patterns like "from Acme", "vendor Acme", "Acme Corp", "by Acme"
        vendor_patterns = [
            r"(?:from|vendor|by)\s+([A-Z][A-Za-z\s&]+?)(?:\s|$|,|\.)",
            r"([A-Z][A-Za-z\s&]+?)\s+(?:corp|corporation|inc|llc|ltd|company)",
        ]
        for pattern in vendor_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                vendor_name = match.group(1).strip()
                # Filter out common false positives
                if vendor_name.lower() not in ["the", "a", "an", "this", "that"]:
                    params["vendor_name"] = vendor_name
                    break

        # Extract invoice number
        # Look for patterns like "INV-2024-001", "invoice 123"
        invoice_pattern = r"(?:invoice|inv)[\s#-]*([A-Z0-9-]+)"
        match = re.search(invoice_pattern, query_lower, re.IGNORECASE)
        if match:
            params["invoice_number"] = match.group(1).upper()

        # Extract date mentions (simplified)
        # Look for patterns like "in December 2024", "this month", "last month", "2024-12"
        # Month names
        month_names = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        ]
        for i, month in enumerate(month_names, 1):
            if month in query_lower:
                # Try to extract year
                year_match = re.search(r"\b(20\d{2})\b", query)
                if year_match:
                    params["year"] = int(year_match.group(1))
                    params["month"] = i
                else:
                    # Just month, assume current year or no year filter
                    params["month"] = i
                break

        # Date range patterns: "from X to Y", "between X and Y"
        date_range_pattern = r"(?:from|between)\s+([A-Za-z0-9\s,]+?)\s+(?:to|and)\s+([A-Za-z0-9\s,]+)"
        match = re.search(date_range_pattern, query_lower)
        if match:
            # Simple extraction - in production would parse actual dates
            params["date_range_start"] = match.group(1).strip()
            params["date_range_end"] = match.group(2).strip()

        # Relative dates: "this month", "last month", "this year", "last year"
        if "this month" in query_lower:
            from datetime import datetime
            now = datetime.now()
            params["month"] = now.month
            params["year"] = now.year
        elif "last month" in query_lower:
            from datetime import datetime, timedelta
            last_month = datetime.now() - timedelta(days=30)
            params["month"] = last_month.month
            params["year"] = last_month.year
        elif "this year" in query_lower:
            from datetime import datetime
            params["year"] = datetime.now().year
        elif "last year" in query_lower:
            from datetime import datetime
            params["year"] = datetime.now().year - 1

        return params

    def _extract_aggregate_params(self, query: str) -> Dict[str, Any]:
        """Extract aggregate query parameters."""
        params: Dict[str, Any] = {}
        query_lower = query.lower()

        # Determine aggregation type
        if "total" in query_lower or "sum" in query_lower:
            params["aggregation_type"] = "sum"
        elif "count" in query_lower or "how many" in query_lower:
            params["aggregation_type"] = "count"
        elif "average" in query_lower or "avg" in query_lower:
            params["aggregation_type"] = "average"
        elif "max" in query_lower or "highest" in query_lower:
            params["aggregation_type"] = "max"
        elif "min" in query_lower or "lowest" in query_lower:
            params["aggregation_type"] = "min"
        else:
            params["aggregation_type"] = "sum"  # default

        # Extract filter parameters
        filter_params = self._extract_filter_params(query)
        params.update(filter_params)

        return params

