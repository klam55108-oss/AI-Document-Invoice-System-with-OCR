"""Streamlit dashboard for reviewing processed invoices."""

import streamlit as st
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.database import get_session
from core.logging import configure_logging, get_logger
from core.models import ExtractedData, Invoice, ProcessingStatus, ValidationResult, ValidationStatus
from interface.dashboard.queries import get_invoice_list, get_invoice_detail

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
    tab1, tab2 = st.tabs(["Invoice List", "Invoice Detail"])

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
        
        if st.button("Reset All Filters"):
            st.rerun()

    # Shared state for selection
    if "selected_invoice_id" not in st.session_state:
        st.session_state.selected_invoice_id = None

    with tab1:
        selected_id = display_invoice_list(status_filter, search_query, date_range)
        if selected_id:
            st.session_state.selected_invoice_id = selected_id
            # Switch to tab2 is handled via streamlit-native behavior if we use session_state properly
            # In simple streamlit, we might need a button or just rely on the user clicking the tab
            # after seeing the selection was captured. 
            # But we can try to force a rerun if needed.
            st.success(f"Selected: {selected_id[:8]}... Switch to 'Invoice Detail' to view.")

    with tab2:
        display_invoice_detail(st.session_state.selected_invoice_id)


def display_invoice_list(status_filter: str, search_query: str = None, date_range: tuple = None):
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
    import asyncio

    try:
        # Use asyncio.run() which properly manages event loop lifecycle
        # This ensures clean state for each request
        invoices = asyncio.run(get_invoice_list(status_enum, search_query, date_range))
    except Exception as e:
        st.error(f"Error loading invoices: {str(e)}")
        logger.error("Failed to load invoices", error=str(e), exc_info=True)
        return

    if not invoices:
        st.info("No invoices found. Process some invoice files to get started.")
        return

    # Fetch all invoices for global metrics
    try:
        all_invoices = asyncio.run(get_invoice_list(None))
    except Exception as e:
        st.error(f"Error loading global metrics: {str(e)}")
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

    if not invoices:
        st.info(f"No invoices found matching your criteria.")
        return

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
        use_container_width=True,
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
                format="%.0f%%",
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

        # Display invoice information
        col1, col2, col3 = st.columns([1, 1, 1.5])

        with col1:
            st.subheader("Invoice Info")
            st.write(f"**Name:** {invoice_detail['file_name']}")
            st.write(f"**Type:** {invoice_detail['file_type'].upper()}")
            st.write(f"**Version:** {invoice_detail['version']}")
            st.write(f"**Created:** {invoice_detail['created_at'].strftime('%Y-%m-%d %H:%M') if invoice_detail['created_at'] else '—'}")

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
            file_path = invoice_detail.get("file_path")
            file_type = invoice_detail.get("file_type", "").lower()
            
            if file_path:
                import os
                if os.path.exists(file_path):
                    if file_type in ["jpg", "jpeg", "png"]:
                        st.image(file_path, use_container_width=True, caption=invoice_detail['file_name'])
                    elif file_type == "pdf":
                        st.info("📂 PDF Preview not available in this view. Please refer to local file.")
                        st.caption(f"Path: `{file_path}`")
                    else:
                        st.info(f"📄 {file_type.upper()} File")
                        st.caption(f"Path: `{file_path}`")
                else:
                    st.warning("⚠️ Source file not found on disk")
                    st.caption(f"Expected at: `{file_path}`")

        # Display extracted data
        if invoice_detail.get("extracted_data"):
            st.divider()
            st.subheader("📊 Extracted Data")
            extracted = invoice_detail["extracted_data"]
            
            # Basic Information
            col1, col2, col3 = st.columns(3)
            with col1:
                vendor = extracted.get("vendor_name")
                st.metric("Vendor", vendor or "—")
            with col2:
                inv_num = extracted.get("invoice_number")
                st.metric("Invoice Number", inv_num or "—")
            with col3:
                inv_date = extracted.get("invoice_date")
                date_str = str(inv_date) if inv_date else "—"
                st.metric("Invoice Date", date_str)
            
            # Financial Information
            st.markdown("#### 💰 Financial Details")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            currency = extracted.get("currency", "USD")
            
            with col1:
                subtotal = extracted.get("subtotal")
                if subtotal is not None:
                    st.metric("Subtotal", f"{currency} {subtotal:,.2f}")
                else:
                    st.metric("Subtotal", "—")
            
            with col2:
                tax_rate = extracted.get("tax_rate")
                if tax_rate is not None:
                    st.metric("Tax Rate", f"{tax_rate * 100:.2f}%")
                else:
                    st.metric("Tax Rate", "—")
            
            with col3:
                tax = extracted.get("tax_amount")
                if tax is not None:
                    st.metric("Tax Amount", f"{currency} {tax:,.2f}")
                else:
                    st.metric("Tax Amount", "—")
            
            with col4:
                total = extracted.get("total_amount")
                if total is not None:
                    st.metric("Total Amount", f"{currency} {total:,.2f}", delta=None)
                else:
                    st.metric("Total Amount", "—")
            
            with col5:
                confidence = extracted.get("extraction_confidence")
                if confidence is not None:
                    conf_pct = float(confidence) * 100
                    st.metric("Confidence", f"{conf_pct:.1f}%", help="AI extraction confidence")
                else:
                    st.metric("Confidence", "—")
            
            # Due Date
            due_date = extracted.get("due_date")
            if due_date:
                st.caption(f"📅 **Due Date:** {due_date}")
            
            # Line Items
            line_items = extracted.get("line_items")
            if line_items:
                st.markdown("#### 📋 Line Items")
                if isinstance(line_items, list) and len(line_items) > 0:
                    line_items_data = []
                    for item in line_items:
                        if isinstance(item, dict):
                            line_items_data.append({
                                "Description": item.get("description", "—"),
                                "Quantity": item.get("quantity", "—"),
                                "Unit Price": f"{currency} {item.get('unit_price', 0):,.2f}" if item.get("unit_price") else "—",
                                "Amount": f"{currency} {item.get('amount', 0):,.2f}" if item.get("amount") else "—",
                            })
                    if line_items_data:
                        st.dataframe(pd.DataFrame(line_items_data), use_container_width=True, hide_index=True)
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
                    render_validation_item(result)
            
            # Display Warning Rules
            if warning_list:
                st.markdown("### ⚠️ Warnings")
                for result in warning_list:
                    render_validation_item(result)
            
            # Display Passed Rules (collapsed)
            if passed_list:
                with st.expander(f"✅ View {len(passed_list)} Passed Rules"):
                    for result in passed_list:
                        render_validation_item(result)
        else:
            st.info("ℹ️ No validation results available. The invoice may still be processing.")


def render_validation_item(result):
    """Helper to render a validation result item."""
    status = result.get("status", "").lower()
    rule_name = result.get("rule_name", "Unknown Rule")
    rule_desc = result.get("rule_description", "")
    
    # Emoji based on status
    status_emoji = '✅' if status == 'passed' else '❌' if status == 'failed' else '⚠️'
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{status_emoji} {rule_name}**")
            if rule_desc:
                st.caption(rule_desc)
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
            st.error(error_msg)
        
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

