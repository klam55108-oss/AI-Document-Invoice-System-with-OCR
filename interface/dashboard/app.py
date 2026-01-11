"""Streamlit dashboard for reviewing processed invoices."""

from datetime import datetime

import asyncio
import pandas as pd
import os
import streamlit as st
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.database import get_session
from core.logging import configure_logging, get_logger
from core.models import ExtractedData, Invoice, ProcessingStatus, ValidationResult, ValidationStatus
from interface.dashboard.queries import (
    get_financial_summary_data,
    get_invoice_detail,
    get_invoice_list,
    get_status_distribution,
    get_time_series_data,
    get_vendor_analysis_data,
)
from interface.dashboard.components.charts import (
    create_financial_summary_charts,
    create_status_distribution_chart,
    create_time_series_chart,
    create_vendor_analysis_chart,
)
from interface.dashboard.components.export_utils import (
    export_invoice_detail_to_pdf,
    export_invoice_list_to_csv,
)
from interface.dashboard.utils.data_formatters import (
    enhance_validation_result,
    format_missing_field,
)
from interface.dashboard.utils.path_resolver import resolve_file_path
from interface.dashboard.components.chatbot import render_chatbot_tab
from interface.dashboard.components.quality_dashboard import render_quality_dashboard
from interface.dashboard.components.file_preview import (
    render_file_preview,
    render_extracted_data_with_confidence,
)

# Configure logging
configure_logging(log_level="INFO", log_format="json")
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="E-Invoice Review Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database connection (simplified for scaffold)
# In production, this would use dependency injection
_engine = None
_session_factory = None


def get_status_value(status) -> str:
    """Helper to get string value from either enum or string."""
    if status is None:
        return ""
    return status.value if hasattr(status, 'value') else str(status)


def init_db_connection():
    """Initialize database connection for dashboard."""
    global _engine, _session_factory
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            st.error("DATABASE_URL not set. Please configure .env file.")
            st.stop()

        _engine = create_async_engine(database_url, echo=False)
        _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    """Get database session."""
    if _session_factory is None:
        init_db_connection()
    return _session_factory()


def main():
    """Main dashboard application."""
    st.title("📄 E-Invoice Review Dashboard")
    st.markdown("Review processed invoices, extracted data, and validation results")

    # Initialize database
    init_db_connection()

    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Invoice List", "Invoice Detail", "Upload Files", "Chatbot", "Quality Metrics"])

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        status_filter = st.selectbox(
            "Processing Status",
            ["All", "Pending", "Queued", "Processing", "Completed", "Failed"],
            index=0,
        )
        
        search_query = st.text_input("Search Invoices", placeholder="File name or vendor...")
        
        date_range = st.date_input(
            "Date Range",
            value=[],
            help="Filter by creation date"
        )
        
        st.divider()
        st.subheader("Advanced Filters")
        
        vendor_filter = st.text_input("Vendor Name", placeholder="Filter by vendor...", help="Partial match on vendor name")
        
        col_amount1, col_amount2 = st.columns(2)
        with col_amount1:
            amount_min = st.number_input("Min Amount", min_value=0.0, value=None, step=100.0, help="Minimum total amount")
        with col_amount2:
            amount_max = st.number_input("Max Amount", min_value=0.0, value=None, step=100.0, help="Maximum total amount")
        
        confidence_min = st.slider(
            "Min Confidence",
            min_value=0.0,
            max_value=1.0,
            value=None,
            step=0.05,
            help="Minimum extraction confidence (0.0-1.0)"
        )
        
        validation_status_filter = st.selectbox(
            "Validation Status",
            ["All", "All Passed", "Has Failed", "Has Warning"],
            index=0,
            help="Filter by validation results"
        )
        
        if st.button("Reset All Filters"):
            st.rerun()

    # Shared state for selection
    if "selected_invoice_id" not in st.session_state:
        st.session_state.selected_invoice_id = None

    with tab1:
        # Map validation status filter
        validation_status_map = {
            "All": None,
            "All Passed": "all_passed",
            "Has Failed": "has_failed",
            "Has Warning": "has_warning",
        }
        validation_status = validation_status_map.get(validation_status_filter, None)
        
        selected_id = display_invoice_list(
            status_filter,
            search_query,
            date_range,
            vendor=vendor_filter if vendor_filter else None,
            amount_min=amount_min,
            amount_max=amount_max,
            confidence_min=confidence_min,
            validation_status=validation_status,
        )
        if selected_id:
            st.session_state.selected_invoice_id = selected_id
            # Switch to tab2 is handled via streamlit-native behavior if we use session_state properly
            # In simple streamlit, we might need a button or just rely on the user clicking the tab
            # after seeing the selection was captured. 
            # But we can try to force a rerun if needed.
            st.success(f"Selected: {selected_id[:8]}... Switch to 'Invoice Detail' to view.")

    with tab2:
        display_invoice_detail(st.session_state.selected_invoice_id)

    with tab3:
        from interface.dashboard.components.upload import render_upload_ui
        from core.config import settings
        api_port = os.getenv("API_PORT", str(settings.API_PORT))
        render_upload_ui(api_base_url=f"http://127.0.0.1:{api_port}")

    with tab4:
        render_chatbot_tab()
    
    with tab5:
        from interface.dashboard.components.quality_dashboard import fetch_quality_data, render_quality_dashboard_ui
        st.header("📊 Extraction Quality Dashboard")
        st.markdown("Monitor extraction accuracy, confidence scores, and data quality metrics.")

        async def get_quality_data():
            async with _session_factory() as session:
                return await fetch_quality_data(session)
        
        try:
            summary, by_format, low_confidence = asyncio.run(get_quality_data())
            render_quality_dashboard_ui(summary, by_format, low_confidence)
        except Exception as e:
            logger.error("Failed to render quality dashboard", error=str(e))
            st.error(f"Failed to load quality metrics: {str(e)}")


def display_invoice_list(
    status_filter: str,
    search_query: str = None,
    date_range: tuple = None,
    vendor: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    confidence_min: float | None = None,
    validation_status: str | None = None,
):
    """Display list of processed invoices."""
    st.header("Processed Invoices")

    # Convert status filter
    status_map = {
        "All": None,
        "Pending": ProcessingStatus.PENDING,
        "Queued": ProcessingStatus.QUEUED,
        "Processing": ProcessingStatus.PROCESSING,
        "Completed": ProcessingStatus.COMPLETED,
        "Failed": ProcessingStatus.FAILED,
    }
    status_enum = status_map.get(status_filter)

    # Fetch invoices using proper async handling for Streamlit
    try:
        # Use asyncio.run() which properly manages event loop lifecycle
        # This ensures clean state for each request
        invoices = asyncio.run(
            get_invoice_list(
                status_enum,
                search_query,
                date_range,
                vendor=vendor,
                amount_min=amount_min,
                amount_max=amount_max,
                confidence_min=confidence_min,
                validation_status=validation_status,
            )
        )
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Provide user-friendly error messages
        if "DATABASE_URL" in error_msg or "connection" in error_msg.lower():
            st.error("❌ Database connection error. Please check your database configuration.")
            st.info("💡 Tip: Verify your `.env` file contains a valid `DATABASE_URL`.")
        elif "Failed to retrieve invoices" in error_msg:
            st.error(f"❌ Failed to load invoices: {error_msg}")
            st.info("💡 Tip: Check database logs for more details.")
        else:
            st.error(f"❌ Error loading invoices: {error_msg}")
        
        logger.error("Failed to load invoices", error=str(e), error_type=error_type, exc_info=True)
        return

    if not invoices:
        st.info("No invoices found. Process some invoice files to get started.")
        return

    # Fetch all invoices for global metrics
    try:
        all_invoices = asyncio.run(get_invoice_list(None))
    except Exception as e:
        logger.warning("Failed to load global metrics, continuing without them", error=str(e))
        # Don't show error to user for metrics - just continue without them
        all_invoices = []

    # Display status summary metrics (Global)
    if all_invoices:
        all_invoice_data = [{"Status": get_status_value(inv.processing_status)} for inv in all_invoices]
        all_df = pd.DataFrame(all_invoice_data)
        status_counts = all_df["Status"].value_counts()
        
        # Calculate unique files (by hash)
        unique_hashes = len(set(inv.file_hash for inv in all_invoices if inv.file_hash))
        total_versions = len(all_invoices)
        
        # Advanced Metrics
        completed_invoices = [inv for inv in all_invoices if get_status_value(inv.processing_status) == "completed"]
        avg_confidence = 0
        if completed_invoices:
            conf_list = [float(inv.extracted_data.extraction_confidence) for inv in completed_invoices if inv.extracted_data and inv.extracted_data.extraction_confidence is not None]
            if conf_list:
                avg_confidence = sum(conf_list) / len(conf_list)
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total Records", total_versions, help="Total number of processing attempts")
        with col2:
            st.metric("Unique Files", unique_hashes, help="Number of unique file contents")
        with col3:
            st.metric("✅ Completed", status_counts.get("completed", 0))
        with col4:
            st.metric("❌ Failed", status_counts.get("failed", 0))
        with col5:
            st.metric("🎯 Avg Confidence", f"{avg_confidence*100:.1f}%")
        with col6:
            pending = status_counts.get("processing", 0) + status_counts.get("pending", 0) + status_counts.get("queued", 0)
            st.metric("⏳ In Progress", pending)

    st.divider()

    # Analytics Section
    st.subheader("📊 Analytics")
    
    # Create tabs for different analytics views
    analytics_tab1, analytics_tab2, analytics_tab3, analytics_tab4 = st.tabs([
        "Status Distribution",
        "Processing Trends",
        "Vendor Analysis",
        "Financial Summary"
    ])
    
    with analytics_tab1:
        try:
            status_counts = asyncio.run(get_status_distribution())
            if status_counts:
                fig = create_status_distribution_chart(status_counts)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No status data available")
        except Exception as e:
            st.error(f"Error loading status distribution: {str(e)}")
            logger.error("Failed to load status distribution", error=str(e), exc_info=True)
    
    with analytics_tab2:
        col1, col2 = st.columns([1, 4])
        with col1:
            aggregation = st.selectbox("Aggregation", ["daily", "weekly", "monthly"], key="time_series_agg")
        try:
            time_series = asyncio.run(get_time_series_data(aggregation=aggregation))
            if time_series:
                fig = create_time_series_chart(time_series, aggregation=aggregation)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No time series data available")
        except Exception as e:
            st.error(f"Error loading time series: {str(e)}")
            logger.error("Failed to load time series", error=str(e), exc_info=True)
    
    with analytics_tab3:
        col1, col2 = st.columns([1, 1])
        with col1:
            sort_by = st.selectbox("Sort By", ["count", "amount"], key="vendor_sort")
        with col2:
            limit = st.slider("Top N Vendors", 5, 20, 10, key="vendor_limit")
        try:
            vendor_data = asyncio.run(get_vendor_analysis_data(sort_by=sort_by, limit=limit))
            if vendor_data:
                fig = create_vendor_analysis_chart(vendor_data, sort_by=sort_by, limit=limit)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No vendor data available")
        except Exception as e:
            st.error(f"Error loading vendor analysis: {str(e)}")
            logger.error("Failed to load vendor analysis", error=str(e), exc_info=True)
    
    with analytics_tab4:
        try:
            financial_data = asyncio.run(get_financial_summary_data())
            if financial_data:
                total_fig, tax_fig, currency_fig = create_financial_summary_charts(
                    total_amount=financial_data.get("total_amount", 0.0),
                    tax_breakdown=financial_data.get("tax_breakdown"),
                    currency_distribution=financial_data.get("currency_distribution"),
                )
                
                st.plotly_chart(total_fig, width='stretch')
                
                col1, col2 = st.columns(2)
                if tax_fig:
                    with col1:
                        st.plotly_chart(tax_fig, width='stretch')
                if currency_fig:
                    with col2:
                        st.plotly_chart(currency_fig, width='stretch')
            else:
                st.info("No financial data available")
        except Exception as e:
            st.error(f"Error loading financial summary: {str(e)}")
            logger.error("Failed to load financial summary", error=str(e), exc_info=True)
    
    st.divider()

    if not invoices:
        st.info(f"No invoices found matching your criteria.")
        return

    # Export button
    col_export1, col_export2 = st.columns([1, 10])
    with col_export1:
        try:
            # Prepare invoice data for export
            export_data = []
            for invoice in invoices:
                extracted = invoice.extracted_data
                export_data.append({
                    "invoice_id": str(invoice.id),
                    "file_name": invoice.file_name,
                    "processing_status": get_status_value(invoice.processing_status),
                    "vendor_name": extracted.vendor_name if extracted else None,
                    "total_amount": float(extracted.total_amount) if extracted and extracted.total_amount else None,
                    "currency": extracted.currency if extracted else None,
                    "invoice_date": extracted.invoice_date if extracted else None,
                    "created_at": invoice.created_at,
                })
            
            csv_bytes = export_invoice_list_to_csv(export_data)
            st.download_button(
                label="📥 Export to CSV",
                data=csv_bytes,
                file_name=f"invoices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Export filtered invoice list to CSV file",
            )
        except Exception as e:
            st.error(f"Error preparing CSV export: {str(e)}")
            logger.error("Failed to prepare CSV export", error=str(e), exc_info=True)

    # Bulk Actions
    st.subheader("⚡ Bulk Actions")
    bulk_col1, bulk_col2, bulk_col3 = st.columns([2, 1, 1])
    
    with bulk_col1:
        # Create list of invoice options for bulk selection
        invoice_options = {
            f"{inv.file_name} ({str(inv.id)[:8]}...)": str(inv.id)
            for inv in invoices
        }
        selected_invoices = st.multiselect(
            "Select Invoices for Bulk Action",
            options=list(invoice_options.keys()),
            help="Select multiple invoices to perform bulk operations",
        )
    
    with bulk_col2:
        force_reprocess = st.checkbox("Force Reprocess", value=False, help="Force reprocessing even if already completed")
    
    with bulk_col3:
        if st.button("🔄 Bulk Reprocess", disabled=len(selected_invoices) == 0, type="primary"):
            if selected_invoices:
                # Get invoice IDs from selected options
                invoice_ids = [invoice_options[opt] for opt in selected_invoices]
                
                # Call bulk reprocess API
                import httpx
                try:
                    with st.spinner(f"Reprocessing {len(invoice_ids)} invoice(s)..."):
                        async def bulk_reprocess():
                            from core.config import settings
                            api_port = os.getenv("API_PORT", str(settings.API_PORT))
                            api_base = f"http://127.0.0.1:{api_port}"
                            async with httpx.AsyncClient(timeout=300.0) as client:
                                response = await client.post(
                                    f"{api_base}/api/v1/invoices/bulk/reprocess",
                                    json={
                                        "invoice_ids": invoice_ids,
                                        "force_reprocess": force_reprocess,
                                    },
                                )
                                response.raise_for_status()
                                return response.json()
                        
                        result = asyncio.run(bulk_reprocess())
                        
                        if result.get("status") == "success":
                            st.success(
                                f"✅ Bulk reprocess initiated: "
                                f"{result.get('successful', 0)} successful, "
                                f"{result.get('failed', 0)} failed, "
                                f"{result.get('skipped', 0)} skipped"
                            )
                            # Show detailed results
                            if result.get("results"):
                                with st.expander("View Detailed Results"):
                                    for item in result["results"]:
                                        status_icon = "✅" if item["status"] == "success" else "❌" if item["status"] == "failed" else "⏭️"
                                        st.write(f"{status_icon} {item['invoice_id'][:8]}... - {item['status']}: {item.get('message', '')}")
                            st.rerun()
                        else:
                            st.error(f"Bulk reprocess failed: {result.get('error', 'Unknown error')}")
                except httpx.HTTPStatusError as e:
                    st.error(f"API error: {e.response.status_code} - {e.response.text}")
                except Exception as e:
                    st.error(f"Error during bulk reprocess: {str(e)}")
                    logger.error("Bulk reprocess failed", error=str(e), exc_info=True)
    
    st.divider()

    # Display invoices in an enhanced table
    invoice_data = []
    for invoice in invoices:
        # Handle both enum and string values for processing_status
        status_value = get_status_value(invoice.processing_status)
        
        # Get extracted data summary
        extracted = invoice.extracted_data
        vendor_name = extracted.vendor_name if extracted else None
        total_amount = float(extracted.total_amount) if extracted and extracted.total_amount else None
        currency = extracted.currency if extracted else None
        
        # Get validation summary
        validation_results = invoice.validation_results
        val_summary = "—"
        if validation_results:
            passed = sum(1 for r in validation_results if get_status_value(r.status) == "passed")
            total = len(validation_results)
            failed = sum(1 for r in validation_results if get_status_value(r.status) == "failed")
            warnings = sum(1 for r in validation_results if get_status_value(r.status) == "warning")
            
            if failed > 0:
                val_summary = f"❌ {failed} Failed"
            elif warnings > 0:
                val_summary = f"⚠️ {warnings} Warn"
            else:
                val_summary = f"✅ {passed}/{total}"
        
        # Format file size
        file_size_kb = invoice.file_size / 1024 if invoice.file_size else 0
        file_size_str = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb / 1024:.2f} MB"
        
        # Format hash (show first 8 chars to identify duplicates)
        hash_short = invoice.file_hash[:8] + "..." if invoice.file_hash else "N/A"
        
        # Check if this is a duplicate (same hash exists multiple times)
        is_duplicate = False
        if invoice.file_hash:
            hash_count = sum(1 for inv in invoices if inv.file_hash == invoice.file_hash)
            is_duplicate = hash_count > 1
        
        # Calculate processing duration
        processing_duration = None
        if invoice.processed_at and invoice.created_at:
            duration = invoice.processed_at - invoice.created_at
            total_seconds = duration.total_seconds()
            if total_seconds < 60:
                processing_duration = f"{total_seconds:.1f}s"
            elif total_seconds < 3600:
                processing_duration = f"{total_seconds / 60:.1f}m"
            else:
                processing_duration = f"{total_seconds / 3600:.1f}h"
        
        # Format amount
        amount_str = None
        if total_amount and currency:
            amount_str = f"{currency} {total_amount:,.2f}"
        elif total_amount:
            amount_str = f"${total_amount:,.2f}"
        
        # Add visual indicator for duplicates
        version_indicator = f"v{invoice.version}"
        if is_duplicate:
            version_indicator = f"🔄 {version_indicator}"
        
        # Status with emoji
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "processing": "⏳",
            "pending": "⏸️",
            "queued": "📋"
        }
        status_display = f"{status_emoji.get(status_value.lower(), '')} {status_value.title()}"
        
        # Extraction confidence and validation summary
        confidence = float(extracted.extraction_confidence) if extracted and extracted.extraction_confidence else 0.0
        
        invoice_data.append({
            "ID_Full": str(invoice.id),
            "ID": str(invoice.id)[:8] + "...",
            "File Name": invoice.file_name,
            "Hash": hash_short,
            "Type": invoice.file_type.upper(),
            "Size": file_size_str,
            "Version": version_indicator,
            "Status": status_display,
            "Validation": val_summary,
            "Vendor": vendor_name or "—",
            "Amount": amount_str or "—",
            "Confidence": confidence,
            "Duration": processing_duration or "—",
            "Created": invoice.created_at.strftime("%Y-%m-%d %H:%M") if invoice.created_at else "",
            "Processed": invoice.processed_at.strftime("%Y-%m-%d %H:%M") if invoice.processed_at else "—",
        })

    df = pd.DataFrame(invoice_data)
    
    # Reorder columns for better readability (ensure ID_Full is included for selection)
    column_order = [
        "ID_Full", "ID", "File Name", "Hash", "Type", "Status", "Validation", 
        "Vendor", "Amount", "Confidence", "Duration", "Created"
    ]
    # Filter columns to only those that exist
    column_order = [c for c in column_order if c in df.columns]
    df = df[column_order]
    
    st.write(f"Showing {len(df)} results")
    
    # Use st.dataframe with better formatting and selection
    event = st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "ID_Full": None,  # Hide the full ID
            "ID": st.column_config.TextColumn("ID", width="small"),
            "File Name": st.column_config.TextColumn("File Name", width="medium"),
            "Hash": st.column_config.TextColumn("Hash", width="small", help="First 8 chars of file content hash"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Size": st.column_config.TextColumn("Size", width="small"),
            "Version": st.column_config.TextColumn("Version", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Vendor": st.column_config.TextColumn("Vendor", width="medium"),
            "Amount": st.column_config.TextColumn("Amount", width="medium"),
            "Confidence": st.column_config.ProgressColumn(
                "Confidence",
                help="Extraction confidence score",
                format="%.1f%%",
                min_value=0,
                max_value=1,
            ),
            "Duration": st.column_config.TextColumn("Duration", width="small", help="Processing time"),
            "Created": st.column_config.TextColumn("Created", width="medium"),
            "Processed": st.column_config.TextColumn("Processed", width="medium"),
        }
    )
    
    # Check if a row was selected
    if event and event.selection and event.selection.get("rows"):
        selected_row_idx = event.selection["rows"][0]
        return df.iloc[selected_row_idx]["ID_Full"]
    
    return None
    
    # Add expandable section for additional metadata
    with st.expander("📊 View Detailed Metadata"):
        st.markdown("### File & Processing Metadata")
        st.markdown("""
        - **Hash**: SHA-256 hash of file content (used for duplicate detection)
        - **Version**: Increments when the same file is reprocessed
        - **Duration**: Time taken to process the invoice
        - **Status**: Current processing state (Pending → Queued → Processing → Completed/Failed)
        """)
        
        # Show duplicate detection info
        if len(invoices) > 0:
            hash_counts = {}
            for inv in invoices:
                hash_key = inv.file_hash[:8] if inv.file_hash else "unknown"
                hash_counts[hash_key] = hash_counts.get(hash_key, 0) + 1
            
            duplicates = {k: v for k, v in hash_counts.items() if v > 1}
            if duplicates:
                st.markdown("### 🔄 Duplicate Files Detected")
                for hash_short, count in duplicates.items():
                    st.write(f"- Hash `{hash_short}...` appears **{count} times** (different versions)")


def display_invoice_detail(preselected_id: str = None):
    """Display detailed invoice information."""
    st.header("Invoice Detail")
    
    # Export button (will be enabled after invoice is loaded)
    export_col1, export_col2 = st.columns([1, 10])
    
    # Initialize session state for invoice filtering if it doesn't exist
    if "detail_invoice_id" not in st.session_state:
        st.session_state.detail_invoice_id = preselected_id
    
    # If a new preselected ID is provided, update the session state
    if preselected_id and preselected_id != st.session_state.detail_invoice_id:
        st.session_state.detail_invoice_id = preselected_id
    
    # Get list of invoices for dropdown
    import asyncio
    
    try:
        all_invoices = asyncio.run(get_invoice_list(None))
    except Exception as e:
        st.error(f"Error loading invoice list: {str(e)}")
        all_invoices = []
    
    # Create two columns for input methods
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if all_invoices:
            invoice_options = {
                f"{inv.file_name} (v{inv.version}) - {str(inv.id)[:8]}...": str(inv.id)
                for inv in sorted(all_invoices, key=lambda x: x.created_at, reverse=True)
            }
            # Find index of preselected id if available
            default_index = 0
            if st.session_state.detail_invoice_id:
                for i, inv_id in enumerate(invoice_options.values()):
                    if inv_id == st.session_state.detail_invoice_id:
                        default_index = i + 1
                        break

            selected_invoice = st.selectbox(
                "Select Invoice from List",
                options=[""] + list(invoice_options.keys()),
                index=default_index,
                help="Choose an invoice from the dropdown, or enter UUID manually below"
            )
            
            if selected_invoice and selected_invoice in invoice_options:
                invoice_id_input = invoice_options[selected_invoice]
                st.session_state.detail_invoice_id = invoice_id_input
            else:
                invoice_id_input = None
        else:
            invoice_id_input = None
            st.info("No invoices available. Process some invoices first.")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if all_invoices:
            st.caption(f"📄 {len(all_invoices)} invoices available")
    
    # Method 2: Manual UUID input
    if not invoice_id_input:
        invoice_id_input = st.text_input(
            "Or Enter Invoice ID (UUID) Manually",
            placeholder="123e4567-e89b-12d3-a456-426614174000",
            help="Paste the full UUID from the Invoice List tab or API response"
        )
    
    # Show helper info
    with st.expander("💡 How to get Invoice ID"):
        st.markdown("""
        **Option 1: From Invoice List Tab**
        1. Go to the "Invoice List" tab
        2. Find the invoice you want to view
        3. Copy the full UUID from the "ID" column (click to expand)
        4. Paste it here or use the dropdown above
        
        **Option 2: From API**
        - Use the API endpoint: `GET /api/v1/invoices`
        - Copy the `id` field from the response
        
        **Option 3: From Processing Response**
        - When you process an invoice, the API returns an `invoice_id`
        - Use that UUID here
        """)

    if invoice_id_input:
        import uuid

        try:
            invoice_uuid = uuid.UUID(invoice_id_input)
        except ValueError:
            st.error("❌ Invalid UUID format. Please enter a valid UUID (e.g., 123e4567-e89b-12d3-a456-426614174000)")
            return

        # Show loading state
        with st.spinner("Loading invoice details..."):
            # Fetch invoice detail using proper async handling
            try:
                # Use asyncio.run() which properly manages event loop lifecycle
                # This ensures clean state for each request
                invoice_detail = asyncio.run(get_invoice_detail(invoice_uuid))
            except Exception as e:
                st.error(f"Error loading invoice: {str(e)}")
                logger.error("Failed to load invoice detail", error=str(e), exc_info=True)
                return

        if not invoice_detail:
            st.warning("⚠️ Invoice not found. Please check the Invoice ID and try again.")
            return

        # PDF Export button
        with export_col1:
            try:
                pdf_bytes = export_invoice_detail_to_pdf(invoice_detail)
                st.download_button(
                    label="📥 Export PDF",
                    data=pdf_bytes,
                    file_name=f"invoice_{invoice_detail.get('invoice_id', 'detail')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    help="Export invoice detail to PDF file",
                )
            except Exception as e:
                st.error(f"Error preparing PDF export: {str(e)}")
                logger.error("Failed to prepare PDF export", error=str(e), exc_info=True)

        # Display invoice information
        col1, col2, col3 = st.columns([1, 1, 1.5])

        with col1:
            st.subheader("Invoice Info")
            st.write(f"**Name:** {invoice_detail['file_name']}")
            st.write(f"**Category:** {invoice_detail.get('category', '—')}")
            st.write(f"**Group:** {invoice_detail.get('group', '—')}")
            st.write(f"**Job ID:** {invoice_detail.get('job_id', '—')}")
            st.write(f"**Type:** {invoice_detail['file_type'].upper()}")
            st.write(f"**Version:** {invoice_detail['version']}")
            st.write(f"**Created:** {invoice_detail['created_at'].strftime('%Y-%m-%d %H:%M') if invoice_detail['created_at'] else '—'}")
            
            # Display upload metadata if available
            upload_metadata = invoice_detail.get("upload_metadata")
            if upload_metadata:
                st.divider()
                st.markdown("#### 📤 Upload Information")
                if upload_metadata.get("subfolder"):
                    st.caption(f"**Source Folder:** {upload_metadata['subfolder']}")
                if upload_metadata.get("group"):
                    st.caption(f"**Upload Group:** {upload_metadata['group']}")
                if upload_metadata.get("category"):
                    st.caption(f"**Category:** {upload_metadata['category']}")
                if upload_metadata.get("upload_source"):
                    source_emoji = "🌐" if upload_metadata['upload_source'] == "web-ui" else "📁"
                    st.caption(f"**Upload Source:** {source_emoji} {upload_metadata['upload_source']}")
                if upload_metadata.get("uploaded_at"):
                    st.caption(f"**Uploaded At:** {upload_metadata['uploaded_at']}")

        with col2:
            st.subheader("Processing")
            status = invoice_detail["processing_status"]
            if status == "completed":
                st.success("✅ Completed")
            elif status == "failed":
                st.error("❌ Failed")
                if invoice_detail.get("error_message"):
                    st.caption(f"Error: {invoice_detail['error_message']}")
            else:
                st.info(f"⏳ {status.title()}")
            
            st.write(f"**Processed:** {invoice_detail['processed_at'].strftime('%Y-%m-%d %H:%M') if invoice_detail['processed_at'] else '—'}")

        with col3:
            st.subheader("📄 File Preview")
            render_file_preview(invoice_detail, col_width=400)

        # Display extracted data with confidence scores
        if invoice_detail.get("extracted_data"):
            st.divider()
            extracted = invoice_detail["extracted_data"]
            render_extracted_data_with_confidence(extracted)
            
            # Additional fields
            st.markdown("#### 📋 Additional Information")
            col1, col2 = st.columns(2)
            
            with col1:
                tax_rate = extracted.get("tax_rate")
                if tax_rate is not None:
                    st.metric("Tax Rate", f"{tax_rate * 100:.2f}%")
                else:
                    st.metric("Tax Rate", "—")
            
            with col2:
                due_date = extracted.get("due_date")
                if due_date:
                    st.metric("Due Date", str(due_date))
                else:
                    st.metric("Due Date", "—")
            
            # Line Items
            line_items = extracted.get("line_items")
            if line_items:
                st.markdown("#### 📋 Line Items")
                if isinstance(line_items, list) and len(line_items) > 0:
                    currency = extracted.get("currency", "") or ""
                    line_items_data = []
                    for item in line_items:
                        if isinstance(item, dict):
                            # Helpfully convert string numbers to floats for formatting
                            unit_price = item.get("unit_price")
                            try:
                                unit_price_fmt = f"{currency} {float(unit_price):,.2f}" if unit_price is not None else "—"
                            except (ValueError, TypeError):
                                unit_price_fmt = f"{currency} {unit_price}" if unit_price is not None else "—"
                                
                            amount = item.get("amount")
                            try:
                                amount_fmt = f"{currency} {float(amount):,.2f}" if amount is not None else "—"
                            except (ValueError, TypeError):
                                amount_fmt = f"{currency} {amount}" if amount is not None else "—"

                            line_items_data.append({
                                "Description": item.get("description", "—"),
                                "Quantity": item.get("quantity", "—"),
                                "Unit Price": unit_price_fmt,
                                "Amount": amount_fmt,
                            })
                    if line_items_data:
                        st.dataframe(pd.DataFrame(line_items_data), width='stretch', hide_index=True)
                else:
                    st.info("No line items available")
            
            # Raw Text (expandable)
            raw_text = extracted.get("raw_text")
            if raw_text:
                with st.expander("📝 View Raw Extracted Text"):
                    st.text_area("Raw Text", raw_text, height=200, disabled=True, label_visibility="collapsed")
        else:
            st.info("ℹ️ No extracted data available. The invoice may still be processing or extraction failed.")

        # Display validation results
        if invoice_detail.get("validation_results"):
            st.divider()
            st.subheader("✅ Validation Analysis")
            validation_results = invoice_detail["validation_results"]
            
            # Count validation statuses
            passed_list = [r for r in validation_results if r.get("status", "").lower() == "passed"]
            failed_list = [r for r in validation_results if r.get("status", "").lower() == "failed"]
            warning_list = [r for r in validation_results if r.get("status", "").lower() == "warning"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Passed", len(passed_list))
            with col2:
                st.metric("❌ Failed", len(failed_list), delta=len(failed_list) if len(failed_list) > 0 else None, delta_color="inverse")
            with col3:
                st.metric("⚠️ Warnings", len(warning_list))
            
            st.markdown("---")
            
            # Display Failed Rules first
            if failed_list:
                st.markdown("### ❌ Failed Rules")
                for result in failed_list:
                    enhanced = enhance_validation_result(
                        rule_name=result.get("rule_name", "Unknown Rule"),
                        rule_description=result.get("rule_description"),
                        status=result.get("status", "failed"),
                        expected_value=result.get("expected_value"),
                        actual_value=result.get("actual_value"),
                        tolerance=result.get("tolerance"),
                        error_message=result.get("error_message"),
                    )
                    render_validation_item(enhanced)
            
            # Display Warning Rules
            if warning_list:
                st.markdown("### ⚠️ Warnings")
                for result in warning_list:
                    enhanced = enhance_validation_result(
                        rule_name=result.get("rule_name", "Unknown Rule"),
                        rule_description=result.get("rule_description"),
                        status=result.get("status", "warning"),
                        expected_value=result.get("expected_value"),
                        actual_value=result.get("actual_value"),
                        tolerance=result.get("tolerance"),
                        error_message=result.get("error_message"),
                    )
                    render_validation_item(enhanced)
            
            # Display Passed Rules (collapsed)
            if passed_list:
                with st.expander(f"✅ View {len(passed_list)} Passed Rules"):
                    for result in passed_list:
                        enhanced = enhance_validation_result(
                            rule_name=result.get("rule_name", "Unknown Rule"),
                            rule_description=result.get("rule_description"),
                            status=result.get("status", "passed"),
                            expected_value=result.get("expected_value"),
                            actual_value=result.get("actual_value"),
                            tolerance=result.get("tolerance"),
                            error_message=result.get("error_message"),
                        )
                        render_validation_item(enhanced)
        else:
            st.info("ℹ️ No validation results available. The invoice may still be processing.")


def render_validation_item(result):
    """Helper to render a validation result item with enhanced display."""
    status = result.get("status", "").lower()
    rule_name = result.get("rule_name", "Unknown Rule")
    rule_desc = result.get("rule_description", "")
    severity = result.get("severity", "medium")
    actionable = result.get("actionable", False)
    suggested_action = result.get("suggested_action")
    
    # Emoji based on status and severity
    if status == 'passed':
        status_emoji = '✅'
        border_color = "green"
    elif status == 'failed':
        status_emoji = '❌'
        border_color = "red" if severity == "high" else "orange"
    else:
        status_emoji = '⚠️'
        border_color = "yellow"
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{status_emoji} {rule_name}**")
            if rule_desc:
                st.caption(rule_desc)
            if severity:
                severity_badge = f"🔴 High" if severity == "high" else f"🟡 Medium" if severity == "medium" else f"🟢 Low"
                st.caption(f"Severity: {severity_badge}")
        with col2:
            validated_at = result.get("validated_at")
            if validated_at:
                if isinstance(validated_at, str):
                    st.caption(f"_{validated_at}_")
                else:
                    st.caption(f"_{validated_at.strftime('%Y-%m-%d %H:%M')}_")
        
        # Details
        error_msg = result.get("error_message")
        if error_msg:
            if status == 'failed':
                st.error(error_msg)
            elif status == 'warning':
                st.warning(error_msg)
            else:
                st.info(error_msg)
        
        # Show suggested action if available
        if actionable and suggested_action:
            st.info(f"💡 **Suggested Action:** {suggested_action}")
        
        expected = result.get("expected_value")
        actual = result.get("actual_value")
        
        if expected is not None or actual is not None:
            c1, c2, c3 = st.columns(3)
            with c1:
                if expected is not None:
                    st.write(f"**Expected:** {expected:,.2f}" if isinstance(expected, (int, float)) else f"**Expected:** {expected}")
            with c2:
                if actual is not None:
                    st.write(f"**Actual:** {actual:,.2f}" if isinstance(actual, (int, float)) else f"**Actual:** {actual}")
            with c3:
                tolerance = result.get("tolerance")
                if tolerance is not None:
                    st.write(f"**Tolerance:** ±{tolerance:,.2f}" if isinstance(tolerance, (int, float)) else f"**Tolerance:** {tolerance}")


if __name__ == "__main__":
    main()

