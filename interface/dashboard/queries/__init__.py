"""Quality metrics queries package."""

# Re-export functions from parent queries.py to maintain backward compatibility
import sys
from pathlib import Path

# Add parent directory to path to import from queries.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from queries import (
        get_financial_summary_data,
        get_status_distribution,
        get_time_series_data,
        get_vendor_analysis_data,
    )
except ImportError:
    # If import fails, define placeholders (shouldn't happen in normal operation)
    pass

# Export quality metrics functions
from .quality_metrics import (
    get_quality_summary,
    get_quality_by_format,
    get_low_confidence_invoices,
    get_vendor_suggestions,
    get_invoice_number_suggestions,
)

__all__ = [
    # From parent queries.py
    "get_financial_summary_data",
    "get_status_distribution",
    "get_time_series_data",
    "get_vendor_analysis_data",
    # From quality_metrics module
    "get_quality_summary",
    "get_quality_by_format",
    "get_low_confidence_invoices",
    "get_vendor_suggestions",
    "get_invoice_number_suggestions",
]

