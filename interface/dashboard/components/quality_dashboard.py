"""Quality metrics dashboard component for Streamlit."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger
from interface.dashboard.queries import (
    get_quality_summary,
    get_quality_by_format,
    get_low_confidence_invoices,
)

logger = get_logger(__name__)


async def fetch_quality_data(session: AsyncSession):
    """Fetch all data needed for the quality dashboard.
    
    Args:
        session: Database session
        
    Returns:
        Tuple of (summary, by_format, low_confidence)
    """
    summary = await get_quality_summary(session)
    by_format = await get_quality_by_format(session)
    low_confidence = await get_low_confidence_invoices(session, confidence_threshold=0.7)
    return summary, by_format, low_confidence


def render_quality_dashboard_ui(summary: Dict[str, Any], by_format: list, low_confidence: list):
    """Render the quality metrics dashboard UI with provided data.
    
    Args:
        summary: Quality summary data
        by_format: Quality by format data
        low_confidence: Low confidence invoices
    """
    # Render summary cards
    _render_summary_cards(summary, len(low_confidence))
    
    # Render charts
    col1, col2 = st.columns(2)
    
    with col1:
        _render_format_quality_chart(by_format)
    
    with col2:
        _render_confidence_distribution_chart(by_format)
    
    # Render field completeness metrics
    st.subheader("📝 Field Extraction Completeness")
    _render_field_completion_metrics(summary)
    
    # Render low confidence invoices table
    if low_confidence:
        st.subheader(f"⚠️ Low Confidence Invoices ({len(low_confidence)})")
        st.markdown(f"Invoices with at least one critical field confidence below 0.7")
        _render_low_confidence_table(low_confidence)


def render_quality_dashboard(session: AsyncSession = None):
    """Render the quality metrics dashboard (Legacy compatibility).
    
    Args:
        session: Database session (optional)
    """
    st.header("📊 Extraction Quality Dashboard")
    st.markdown("Monitor extraction accuracy, confidence scores, and data quality metrics.")
    
    # Fetch quality metrics
    try:
        import asyncio
        
        if session:
            # If session is provided, we try to run in a loop if ones isn't running
            # However, if app.py provides the session, it's usually already in a loop
            # which causes the failure. The new preferred way is render_quality_dashboard_ui.
            try:
                loop = asyncio.get_running_loop()
                # If we have a loop, we can't use asyncio.run
                # This legacy function is problematic in that case.
                st.warning("⚠️ Accessing quality dashboard via legacy method. Some components might not load.")
                return
            except RuntimeError:
                summary, by_format, low_confidence = asyncio.run(fetch_quality_data(session))
                render_quality_dashboard_ui(summary, by_format, low_confidence)
        else:
            # This is also problematic if we don't have a session factory here.
            st.error("No database session provided for quality dashboard.")
            
    except Exception as e:
        logger.error("Failed to render quality dashboard", error=str(e))
        st.error(f"Failed to load quality metrics: {str(e)}")


def _render_summary_cards(summary: Dict[str, Any], low_confidence_count: int):
    """Render summary metric cards.
    
    Args:
        summary: Quality summary data
        low_confidence_count: Number of low confidence invoices
    """
    total = summary["total_invoices"]
    vendor_complete = summary["critical_fields_complete"]["vendor_name"]
    invoice_num_complete = summary["critical_fields_complete"]["invoice_number"]
    total_amount_complete = summary["critical_fields_complete"]["total_amount"]
    
    # Calculate overall completion rate (all critical fields must be present)
    all_fields_complete = min(vendor_complete, invoice_num_complete, total_amount_complete)
    overall_completion = (all_fields_complete / total * 100) if total > 0 else 0
    
    # Calculate STP rate (high confidence and complete)
    stp_rate = ((total - low_confidence_count) / total * 100) if total > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Invoices",
            value=f"{total:,}",
            help="Total number of invoices processed"
        )
    
    with col2:
        st.metric(
            label="Overall Completion",
            value=f"{overall_completion:.1f}%",
            delta=f"{all_fields_complete}/{total}",
            help="Percentage of invoices with all critical fields extracted"
        )
    
    with col3:
        st.metric(
            label="STP Rate",
            value=f"{stp_rate:.1f}%",
            delta=f"{total - low_confidence_count}/{total}",
            help="Straight-Through Processing rate (high confidence invoices)"
        )
    
    with col4:
        failed_count = total - all_fields_complete
        st.metric(
            label="Failed Extractions",
            value=f"{failed_count:,}",
            delta=f"-{failed_count / total * 100:.1f}%" if total > 0 else "0%",
            delta_color="inverse",
            help="Invoices with at least one critical field missing"
        )


def _render_format_quality_chart(by_format: list):
    """Render format-wise quality comparison chart.
    
    Args:
        by_format: Quality metrics grouped by format
    """
    if not by_format:
        st.info("No data available for format comparison.")
        return
    
    st.subheader("📈 Quality by File Format")
    
    # Prepare data for chart
    df = pd.DataFrame(by_format)
    
    # Calculate completion percentage
    df["completion_pct"] = (df["vendor_extracted"] / df["total"] * 100).round(1)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    # Convert confidence scores to percentage for better visualization
    df["avg_vendor_conf_pct"] = (df["avg_vendor_conf"] * 100).round(1)
    df["avg_invoice_num_conf_pct"] = (df["avg_invoice_num_conf"] * 100).round(1)
    df["avg_total_conf_pct"] = (df["avg_total_conf"] * 100).round(1)
    
    fig.add_trace(go.Bar(
        name="Vendor Name",
        x=df["file_type"],
        y=df["avg_vendor_conf_pct"],
        text=[f"{val:.1f}%" for val in df["avg_vendor_conf_pct"]],
        textposition="auto",
        marker_color="rgb(55, 83, 109)"
    ))
    
    fig.add_trace(go.Bar(
        name="Invoice Number",
        x=df["file_type"],
        y=df["avg_invoice_num_conf_pct"],
        text=[f"{val:.1f}%" for val in df["avg_invoice_num_conf_pct"]],
        textposition="auto",
        marker_color="rgb(26, 118, 255)"
    ))
    
    fig.add_trace(go.Bar(
        name="Total Amount",
        x=df["file_type"],
        y=df["avg_total_conf_pct"],
        text=[f"{val:.1f}%" for val in df["avg_total_conf_pct"]],
        textposition="auto",
        marker_color="rgb(50, 171, 96)"
    ))
    
    fig.update_layout(
        barmode="group",
        xaxis_title="File Type",
        yaxis_title="Average Confidence Score (%)",
        yaxis_range=[0, 100],
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Show data table
    with st.expander("📊 View detailed data"):
        display_df = df[[
            "file_type",
            "total",
            "vendor_extracted",
            "completion_pct",
            "avg_vendor_conf",
            "avg_invoice_num_conf",
            "avg_total_conf"
        ]].copy()
        # Convert confidence to percentage for display
        display_df["avg_vendor_conf"] = (display_df["avg_vendor_conf"] * 100).round(1)
        display_df["avg_invoice_num_conf"] = (display_df["avg_invoice_num_conf"] * 100).round(1)
        display_df["avg_total_conf"] = (display_df["avg_total_conf"] * 100).round(1)
        
        display_df.columns = [
            "File Type",
            "Total",
            "Vendor Extracted",
            "Completion %",
            "Avg Vendor Conf %",
            "Avg Invoice# Conf %",
            "Avg Total Conf %"
        ]
        st.dataframe(display_df, width="stretch")


def _render_confidence_distribution_chart(by_format: list):
    """Render confidence score distribution chart.
    
    Args:
        by_format: Quality metrics grouped by format
    """
    if not by_format:
        st.info("No data available for confidence distribution.")
        return
    
    st.subheader("📊 Confidence Score Distribution")
    
    # Prepare data
    df = pd.DataFrame(by_format)
    
    # Calculate average confidence across all fields
    df["avg_confidence"] = df[[
        "avg_vendor_conf",
        "avg_invoice_num_conf",
        "avg_total_conf"
    ]].mean(axis=1)
    
    # Create pie chart for format distribution
    fig = px.pie(
        df,
        values="total",
        names="file_type",
        title="Invoice Distribution by Format",
        color_discrete_sequence=px.colors.sequential.RdBu,
        hole=0.4
    )
    
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )
    
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, width="stretch")
    
    # Show average confidence by format
    with st.expander("📈 Average confidence by format"):
        # Convert to percentage for display
        df["avg_confidence_pct"] = (df["avg_confidence"] * 100).round(1)
        
        fig_bar = px.bar(
            df,
            x="file_type",
            y="avg_confidence_pct",
            text="avg_confidence_pct",
            color="avg_confidence_pct",
            color_continuous_scale="RdYlGn",
            range_color=[0, 100]
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_bar.update_layout(
            xaxis_title="File Type",
            yaxis_title="Average Confidence (%)",
            yaxis_range=[0, 100],
            showlegend=False
        )
        st.plotly_chart(fig_bar, width="stretch")


def _render_field_completion_metrics(summary: Dict[str, Any]):
    """Render field completion metrics.
    
    Args:
        summary: Quality summary data
    """
    total = summary["total_invoices"]
    
    if total == 0:
        st.info("No invoices to analyze.")
        return
    
    # Create completion data
    fields = [
        ("Vendor Name", summary["critical_fields_complete"]["vendor_name"]),
        ("Invoice Number", summary["critical_fields_complete"]["invoice_number"]),
        ("Invoice Date", summary["critical_fields_complete"]["invoice_date"]),
        ("Total Amount", summary["critical_fields_complete"]["total_amount"]),
        ("Subtotal", summary["critical_fields_complete"]["subtotal"]),
        ("Tax Amount", summary["critical_fields_complete"]["tax_amount"]),
        ("Currency", summary["critical_fields_complete"]["currency"]),
    ]
    
    # Create dataframe
    df = pd.DataFrame(fields, columns=["Field", "Extracted"])
    df["Missing"] = total - df["Extracted"]
    df["Completion %"] = (df["Extracted"] / total * 100).round(1)
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Extracted",
        y=df["Field"],
        x=df["Extracted"],
        orientation="h",
        marker_color="rgb(50, 171, 96)",
        text=df["Extracted"],
        textposition="inside"
    ))
    
    fig.add_trace(go.Bar(
        name="Missing",
        y=df["Field"],
        x=df["Missing"],
        orientation="h",
        marker_color="rgb(219, 64, 82)",
        text=df["Missing"],
        textposition="inside"
    ))
    
    fig.update_layout(
        barmode="stack",
        xaxis_title="Number of Invoices",
        yaxis_title="",
        height=300,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Show completion table
    with st.expander("📋 View completion details"):
        display_df = df.copy()
        display_df["Total"] = total
        display_df = display_df[["Field", "Extracted", "Missing", "Total", "Completion %"]]
        st.dataframe(display_df, width="stretch", hide_index=True)


def _render_low_confidence_table(low_confidence: list):
    """Render table of low confidence invoices.
    
    Args:
        low_confidence: List of low confidence invoice records
    """
    if not low_confidence:
        st.success("✅ No low confidence invoices found!")
        return
    
    # Convert to dataframe
    df = pd.DataFrame(low_confidence)
    
    # Format columns (convert confidence to percentage)
    display_df = pd.DataFrame({
        "Invoice ID": df["invoice_id"],
        "File Name": df["file_name"],
        "File Type": df["file_type"],
        "Vendor Conf.": df["vendor_confidence"].apply(lambda x: f"{x*100:.1f}%" if x is not None else "N/A"),
        "Invoice# Conf.": df["invoice_num_confidence"].apply(lambda x: f"{x*100:.1f}%" if x is not None else "N/A"),
        "Total Conf.": df["total_confidence"].apply(lambda x: f"{x*100:.1f}%" if x is not None else "N/A"),
        "Vendor Name": df["vendor_name"].apply(lambda x: x if x else "❌ Missing"),
        "Invoice Number": df["invoice_number"].apply(lambda x: x if x else "❌ Missing"),
        "Total Amount": df["total_amount"].apply(lambda x: f"${x:,.2f}" if x is not None else "❌ Missing"),
    })
    
    # Display table
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Vendor Conf.": st.column_config.TextColumn("Vendor Conf."),
            "Invoice# Conf.": st.column_config.TextColumn("Invoice# Conf."),
            "Total Conf.": st.column_config.TextColumn("Total Conf."),
        }
    )
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Low Confidence Invoices (CSV)",
        data=csv,
        file_name=f"low_confidence_invoices_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

