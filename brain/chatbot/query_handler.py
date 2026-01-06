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

        # Extract vendor name (simple pattern matching)
        # Look for patterns like "from Acme", "vendor Acme", "Acme Corp"
        # This is simplified - production would use NER or LLM

        # Extract invoice number
        # Look for patterns like "INV-2024-001", "invoice 123"
        import re

        invoice_pattern = r"(?:invoice|inv)[\s#-]*([A-Z0-9-]+)"
        match = re.search(invoice_pattern, query_lower, re.IGNORECASE)
        if match:
            params["invoice_number"] = match.group(1).upper()

        # Extract date mentions (simplified)
        # Production would use date parsing library

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

