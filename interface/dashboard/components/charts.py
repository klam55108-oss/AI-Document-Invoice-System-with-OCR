"""Chart generation utilities for dashboard analytics."""

from typing import Any

import plotly.graph_objects as go


def create_status_distribution_chart(
    status_counts: dict[str, int],
    title: str = "Invoice Processing Status Distribution",
) -> go.Figure:
    """Create a pie chart showing invoice processing status distribution.

    Args:
        status_counts: Dictionary mapping status names to counts
            Example: {"completed": 150, "failed": 10, "processing": 5}
        title: Chart title

    Returns:
        Plotly figure object
    """
    if not status_counts:
        # Return empty chart if no data
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    labels = list(status_counts.keys())
    values = list(status_counts.values())

    # Color mapping for statuses
    color_map = {
        "completed": "#28a745",
        "failed": "#dc3545",
        "processing": "#ffc107",
        "pending": "#6c757d",
        "queued": "#17a2b8",
    }

    colors = [color_map.get(label.lower(), "#6c757d") for label in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title=title,
        showlegend=True,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def create_time_series_chart(
    series_data: list[dict[str, Any]],
    aggregation: str = "daily",
    title: str = "Invoice Processing Volume Over Time",
) -> go.Figure:
    """Create a time series chart showing processing volume trends.

    Args:
        series_data: List of dictionaries with "date" and "count" keys
            Example: [{"date": "2025-01-01", "count": 25}, ...]
        aggregation: Time aggregation level ("daily", "weekly", "monthly")
        title: Chart title

    Returns:
        Plotly figure object
    """
    if not series_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    dates = [item["date"] for item in series_data]
    counts = [item["count"] for item in series_data]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=counts,
            mode="lines+markers",
            name="Processing Volume",
            line=dict(color="#007bff", width=2),
            marker=dict(size=8),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Number of Invoices",
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def create_vendor_analysis_chart(
    vendor_data: list[dict[str, Any]],
    sort_by: str = "count",
    title: str = "Top Vendors Analysis",
    limit: int = 10,
) -> go.Figure:
    """Create a bar chart showing top vendors by invoice count or total amount.

    Args:
        vendor_data: List of dictionaries with vendor information
            Example: [{"vendor": "Vendor A", "invoice_count": 50, "total_amount": 100000.00}, ...]
        sort_by: Sort by "count" or "amount"
        title: Chart title
        limit: Number of top vendors to display

    Returns:
        Plotly figure object
    """
    if not vendor_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    # Sort and limit
    sorted_data = sorted(
        vendor_data,
        key=lambda x: x.get("invoice_count" if sort_by == "count" else "total_amount", 0),
        reverse=True,
    )[:limit]

    vendors = [item["vendor"] for item in sorted_data]

    if sort_by == "count":
        values = [item.get("invoice_count", 0) for item in sorted_data]
        yaxis_title = "Number of Invoices"
    else:
        values = [float(item.get("total_amount", 0)) for item in sorted_data]
        yaxis_title = "Total Amount"

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=vendors,
            y=values,
            marker=dict(color="#007bff"),
            text=values,
            textposition="outside",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Vendor",
        yaxis_title=yaxis_title,
        height=400,
        xaxis=dict(tickangle=-45),
        margin=dict(l=20, r=20, t=40, b=100),
    )

    return fig


def create_financial_summary_charts(
    total_amount: float,
    tax_breakdown: list[dict[str, float]] | None = None,
    currency_distribution: list[dict[str, int]] | None = None,
) -> tuple[go.Figure, go.Figure | None, go.Figure | None]:
    """Create financial summary charts.

    Args:
        total_amount: Total amount across all invoices
        tax_breakdown: List of tax rate/amount pairs
            Example: [{"rate": 0.10, "amount": 50000.00}, ...]
        currency_distribution: List of currency counts
            Example: [{"currency": "USD", "count": 100}, ...]

    Returns:
        Tuple of (total amount figure, tax breakdown figure or None, currency figure or None)
    """
    # Total amount metric chart (simple bar)
    total_fig = go.Figure()

    total_fig.add_trace(
        go.Bar(
            x=["Total Amount"],
            y=[total_amount],
            marker=dict(color="#28a745"),
            text=[f"${total_amount:,.2f}"],
            textposition="outside",
        )
    )

    total_fig.update_layout(
        title="Total Invoice Amount",
        yaxis_title="Amount",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    # Tax breakdown chart
    tax_fig = None
    if tax_breakdown:
        tax_fig = go.Figure()

        rates = [f"{item['rate']*100:.1f}%" for item in tax_breakdown]
        amounts = [item["amount"] for item in tax_breakdown]

        tax_fig.add_trace(
            go.Bar(
                x=rates,
                y=amounts,
                marker=dict(color="#ffc107"),
                text=[f"${amt:,.2f}" for amt in amounts],
                textposition="outside",
            )
        )

        tax_fig.update_layout(
            title="Tax Breakdown by Rate",
            xaxis_title="Tax Rate",
            yaxis_title="Amount",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
        )

    # Currency distribution chart
    currency_fig = None
    if currency_distribution:
        currency_fig = go.Figure()

        currencies = [item["currency"] for item in currency_distribution]
        counts = [item["count"] for item in currency_distribution]

        currency_fig.add_trace(
            go.Pie(
                labels=currencies,
                values=counts,
                hole=0.4,
                textinfo="label+percent",
            )
        )

        currency_fig.update_layout(
            title="Currency Distribution",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
        )

    return total_fig, tax_fig, currency_fig

