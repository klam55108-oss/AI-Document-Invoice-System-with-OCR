"""Streamlit dashboard for reviewing processed invoices."""

import streamlit as st
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

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        status_filter = st.selectbox(
            "Processing Status",
            ["All", "Pending", "Queued", "Processing", "Completed", "Failed"],
            index=0,  # Default to All
        )

    # Main content
    tab1, tab2 = st.tabs(["Invoice List", "Invoice Detail"])

    with tab1:
        display_invoice_list(status_filter)

    with tab2:
        display_invoice_detail()


def display_invoice_list(status_filter: str):
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
        invoices = asyncio.run(get_invoice_list(status_enum))
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
        all_invoice_data = [{"Status": inv.processing_status.value} for inv in all_invoices]
        all_df = pd.DataFrame(all_invoice_data)
        status_counts = all_df["Status"].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(all_invoices))
        with col2:
            completed = status_counts.get("completed", 0)
            st.metric("Completed", completed)
        with col3:
            failed = status_counts.get("failed", 0)
            st.metric("Failed", failed)
        with col4:
            processing = status_counts.get("processing", 0) + status_counts.get("pending", 0) + status_counts.get("queued", 0)
            st.metric("In Progress", processing)

    st.divider()

    if not invoices:
        st.info(f"No invoices found with status: {status_filter}")
        return

    # Display invoices in a table
    invoice_data = []
    for invoice in invoices:
        invoice_data.append({
            "ID": str(invoice.id)[:8] + "...",
            "File Name": invoice.file_name,
            "Type": invoice.file_type,
            "Status": invoice.processing_status.value,
            "Version": invoice.version,
            "Created": invoice.created_at.strftime("%Y-%m-%d %H:%M") if invoice.created_at else "",
        })

    df = pd.DataFrame(invoice_data)
    st.write(f"Showing {len(df)} results")
    st.dataframe(df, use_container_width=True, hide_index=True)


def display_invoice_detail():
    """Display detailed invoice information."""
    st.header("Invoice Detail")

    invoice_id_input = st.text_input("Enter Invoice ID (UUID)", placeholder="123e4567-e89b-12d3-a456-426614174000")

    if invoice_id_input:
        import uuid

        try:
            invoice_uuid = uuid.UUID(invoice_id_input)
        except ValueError:
            st.error("Invalid UUID format")
            return

        # Fetch invoice detail using proper async handling
        import asyncio

        try:
            # Use asyncio.run() which properly manages event loop lifecycle
            # This ensures clean state for each request
            invoice_detail = asyncio.run(get_invoice_detail(invoice_uuid))
        except Exception as e:
            st.error(f"Error loading invoice: {str(e)}")
            logger.error("Failed to load invoice detail", error=str(e), exc_info=True)
            return

        if not invoice_detail:
            st.warning("Invoice not found")
            return

        # Display invoice information
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Invoice Information")
            st.write(f"**File Name:** {invoice_detail['file_name']}")
            st.write(f"**File Type:** {invoice_detail['file_type']}")
            st.write(f"**Status:** {invoice_detail['processing_status']}")
            st.write(f"**Version:** {invoice_detail['version']}")
            st.write(f"**Created:** {invoice_detail['created_at']}")

        with col2:
            st.subheader("Processing Status")
            status = invoice_detail["processing_status"]
            if status == "completed":
                st.success("✅ Processing Completed")
            elif status == "failed":
                st.error("❌ Processing Failed")
                if invoice_detail.get("error_message"):
                    st.error(f"Error: {invoice_detail['error_message']}")
            else:
                st.info(f"⏳ Status: {status}")

        # Display extracted data
        if invoice_detail.get("extracted_data"):
            st.subheader("Extracted Data")
            extracted = invoice_detail["extracted_data"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vendor", extracted.get("vendor_name", "N/A"))
            with col2:
                st.metric("Invoice Number", extracted.get("invoice_number", "N/A"))
            with col3:
                st.metric("Invoice Date", str(extracted.get("invoice_date", "N/A")))

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                subtotal = extracted.get("subtotal")
                st.metric("Subtotal", f"${subtotal:.2f}" if subtotal else "N/A")
            with col2:
                tax = extracted.get("tax_amount")
                st.metric("Tax", f"${tax:.2f}" if tax else "N/A")
            with col3:
                total = extracted.get("total_amount")
                st.metric("Total", f"${total:.2f}" if total else "N/A")
            with col4:
                currency = extracted.get("currency", "USD")
                st.metric("Currency", currency)

        # Display validation results
        if invoice_detail.get("validation_results"):
            st.subheader("Validation Results")
            validation_results = invoice_detail["validation_results"]

            for result in validation_results:
                status = result["status"]
                rule_name = result["rule_name"]

                if status == "passed":
                    st.success(f"✅ {rule_name}: Passed")
                elif status == "failed":
                    st.error(f"❌ {rule_name}: Failed")
                    if result.get("error_message"):
                        st.error(f"   {result['error_message']}")
                else:
                    st.warning(f"⚠️ {rule_name}: {status}")

                if result.get("expected_value") and result.get("actual_value"):
                    st.write(f"   Expected: {result['expected_value']}, Actual: {result['actual_value']}")


if __name__ == "__main__":
    main()

