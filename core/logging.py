"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure structured logging."""
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Add sensitive data filter before final renderer
    processors.insert(-1, filter_sensitive_data)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def filter_sensitive_data(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Filter sensitive data from log events."""
    sensitive_fields = [
        "invoice_number",
        "total_amount",
        "subtotal",
        "tax_amount",
        "vendor_name",
        "file_path",
        "encryption_key",
        "password",
    ]

    for field in sensitive_fields:
        if field in event_dict:
            event_dict[field] = "[REDACTED]"

    return event_dict

