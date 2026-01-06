"""Unit tests for chatbot query handler."""

import pytest

from brain.chatbot.query_handler import QueryHandler, QueryIntent


def test_classify_aggregate_query():
    """Test classification of aggregate queries."""
    handler = QueryHandler()

    # Test total/sum queries
    intent = handler.classify_intent("What is the total cost?")
    assert intent.intent_type == QueryHandler.AGGREGATE_QUERY
    assert intent.parameters["aggregation_type"] == "sum"

    # Test count queries
    intent = handler.classify_intent("How many invoices are there?")
    assert intent.intent_type == QueryHandler.AGGREGATE_QUERY
    assert intent.parameters["aggregation_type"] == "count"

    # Test average queries
    intent = handler.classify_intent("What is the average invoice amount?")
    assert intent.intent_type == QueryHandler.AGGREGATE_QUERY
    assert intent.parameters["aggregation_type"] == "average"

    # Test max queries
    intent = handler.classify_intent("What is the highest invoice amount?")
    assert intent.intent_type == QueryHandler.AGGREGATE_QUERY
    assert intent.parameters["aggregation_type"] == "max"

    # Test min queries
    intent = handler.classify_intent("What is the lowest invoice amount?")
    assert intent.intent_type == QueryHandler.AGGREGATE_QUERY
    assert intent.parameters["aggregation_type"] == "min"


def test_classify_list_invoices():
    """Test classification of list invoices queries."""
    handler = QueryHandler()

    intent = handler.classify_intent("Show me all invoices")
    assert intent.intent_type == QueryHandler.LIST_INVOICES

    intent = handler.classify_intent("List invoices from Acme")
    assert intent.intent_type == QueryHandler.LIST_INVOICES

    intent = handler.classify_intent("Find all invoices")
    assert intent.intent_type == QueryHandler.LIST_INVOICES

    intent = handler.classify_intent("Display invoices")
    assert intent.intent_type == QueryHandler.LIST_INVOICES


def test_classify_get_details():
    """Test classification of get details queries."""
    handler = QueryHandler()

    intent = handler.classify_intent("What are the details of invoice INV-001?")
    assert intent.intent_type == QueryHandler.GET_DETAILS

    intent = handler.classify_intent("Tell me about invoice 123")
    assert intent.intent_type == QueryHandler.GET_DETAILS

    intent = handler.classify_intent("What information is in invoice INV-001?")
    assert intent.intent_type == QueryHandler.GET_DETAILS


def test_classify_find_invoice():
    """Test classification of find invoice queries (default)."""
    handler = QueryHandler()

    # Queries that don't match other patterns default to FIND_INVOICE
    intent = handler.classify_intent("Find invoice INV-001")
    assert intent.intent_type == QueryHandler.FIND_INVOICE

    intent = handler.classify_intent("Invoice from Acme Corp")
    assert intent.intent_type == QueryHandler.FIND_INVOICE


def test_extract_invoice_number():
    """Test extraction of invoice number from query."""
    handler = QueryHandler()

    intent = handler.classify_intent("Show me invoice INV-2024-001")
    assert "invoice_number" in intent.parameters
    assert intent.parameters["invoice_number"] == "INV-2024-001"

    intent = handler.classify_intent("What is invoice #123?")
    assert "invoice_number" in intent.parameters
    assert intent.parameters["invoice_number"] == "123"

    intent = handler.classify_intent("Find invoice INV-ABC-123")
    assert "invoice_number" in intent.parameters
    assert intent.parameters["invoice_number"] == "INV-ABC-123"


def test_extract_aggregate_params():
    """Test extraction of aggregate query parameters."""
    handler = QueryHandler()

    intent = handler.classify_intent("What is the total cost of invoices from Acme?")
    assert intent.intent_type == QueryHandler.AGGREGATE_QUERY
    assert intent.parameters["aggregation_type"] == "sum"


def test_query_confidence():
    """Test that queries have confidence scores."""
    handler = QueryHandler()

    intent = handler.classify_intent("How many invoices?")
    assert hasattr(intent, "confidence")
    assert 0.0 <= intent.confidence <= 1.0


def test_case_insensitive():
    """Test that query classification is case insensitive."""
    handler = QueryHandler()

    intent1 = handler.classify_intent("HOW MANY INVOICES?")
    intent2 = handler.classify_intent("how many invoices?")
    intent3 = handler.classify_intent("How Many Invoices?")

    assert intent1.intent_type == intent2.intent_type == intent3.intent_type
    assert intent1.intent_type == QueryHandler.AGGREGATE_QUERY


def test_empty_query():
    """Test handling of empty or whitespace queries."""
    handler = QueryHandler()

    intent = handler.classify_intent("")
    assert intent.intent_type == QueryHandler.FIND_INVOICE

    intent = handler.classify_intent("   ")
    assert intent.intent_type == QueryHandler.FIND_INVOICE

