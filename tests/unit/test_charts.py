"""Unit tests for chart generation utilities."""

import pytest
from plotly.graph_objects import Figure

from interface.dashboard.components.charts import (
    create_financial_summary_charts,
    create_status_distribution_chart,
    create_time_series_chart,
    create_vendor_analysis_chart,
)


def test_create_status_distribution_chart():
    """Test status distribution chart generation with valid data."""
    status_counts = {"completed": 150, "failed": 10, "processing": 5, "pending": 3}
    
    fig = create_status_distribution_chart(status_counts)
    
    assert isinstance(fig, Figure)
    assert len(fig.data) > 0
    # Verify chart has data
    assert fig.layout.title.text == "Invoice Processing Status Distribution"


def test_create_status_distribution_chart_empty():
    """Test status distribution chart with empty data."""
    status_counts = {}
    
    fig = create_status_distribution_chart(status_counts)
    
    assert isinstance(fig, Figure)
    # Should have annotation for "No data available"
    assert len(fig.layout.annotations) > 0


def test_create_time_series_chart():
    """Test time series chart generation with valid data."""
    time_series = [
        {"date": "2024-01-01", "count": 10},
        {"date": "2024-01-02", "count": 15},
        {"date": "2024-01-03", "count": 12},
    ]
    
    fig = create_time_series_chart(time_series, aggregation="daily")
    
    assert isinstance(fig, Figure)
    assert len(fig.data) > 0


def test_create_time_series_chart_empty():
    """Test time series chart with empty data."""
    time_series = []
    
    fig = create_time_series_chart(time_series, aggregation="daily")
    
    assert isinstance(fig, Figure)
    # Should handle empty data gracefully


def test_create_vendor_analysis_chart():
    """Test vendor analysis chart generation with valid data."""
    vendor_data = [
        {"vendor_name": "Vendor A", "count": 50, "total_amount": 50000.00},
        {"vendor_name": "Vendor B", "count": 30, "total_amount": 30000.00},
        {"vendor_name": "Vendor C", "count": 20, "total_amount": 20000.00},
    ]
    
    fig = create_vendor_analysis_chart(vendor_data, sort_by="count", limit=10)
    
    assert isinstance(fig, Figure)
    assert len(fig.data) > 0


def test_create_vendor_analysis_chart_empty():
    """Test vendor analysis chart with empty data."""
    vendor_data = []
    
    fig = create_vendor_analysis_chart(vendor_data, sort_by="count", limit=10)
    
    assert isinstance(fig, Figure)
    # Should handle empty data gracefully


def test_create_financial_summary_charts():
    """Test financial summary charts generation with valid data."""
    total_amount = 100000.00
    tax_breakdown = {"VAT": 5000.00, "GST": 3000.00}
    currency_distribution = {"USD": 80000.00, "EUR": 20000.00}
    
    total_fig, tax_fig, currency_fig = create_financial_summary_charts(
        total_amount=total_amount,
        tax_breakdown=tax_breakdown,
        currency_distribution=currency_distribution,
    )
    
    assert isinstance(total_fig, Figure)
    assert isinstance(tax_fig, Figure)
    assert isinstance(currency_fig, Figure)
    assert len(total_fig.data) > 0


def test_create_financial_summary_charts_empty():
    """Test financial summary charts with empty data."""
    total_fig, tax_fig, currency_fig = create_financial_summary_charts(
        total_amount=0.0,
        tax_breakdown=None,
        currency_distribution=None,
    )
    
    assert isinstance(total_fig, Figure)
    # tax_fig and currency_fig may be None if data is missing
    assert tax_fig is None or isinstance(tax_fig, Figure)
    assert currency_fig is None or isinstance(currency_fig, Figure)

