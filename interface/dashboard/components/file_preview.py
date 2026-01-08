"""File preview component for invoice detail tab."""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import base64

from core.logging import get_logger
from interface.dashboard.utils.path_resolver import resolve_file_path

logger = get_logger(__name__)


def render_file_preview(invoice_detail: Dict[str, Any], col_width: int = 400):
    """Render file preview based on file type.
    
    Args:
        invoice_detail: Invoice detail dictionary
        col_width: Width of the preview column in pixels
    """
    storage_path = invoice_detail.get("storage_path")
    file_hash = invoice_detail.get("file_hash")
    file_type = invoice_detail.get("file_type", "").lower()
    file_name = invoice_detail.get("file_name", "Unknown")
    
    if not storage_path:
        st.warning("⚠️ **No file path available**")
        return
    
    # Resolve file path
    resolved = resolve_file_path(storage_path, file_hash=file_hash, data_dir="data")
    
    if not resolved["exists"] or not resolved["resolved_path"]:
        st.warning("⚠️ **Source file not found on disk**")
        st.caption(f"Expected at: `{storage_path}`")
        if resolved.get("error"):
            st.caption(f"💡 {resolved['error']}")
        if file_hash:
            st.caption(f"💡 Also checked encrypted location with hash: `{file_hash[:8]}...`")
        return
    
    resolved_path = Path(resolved["resolved_path"])
    
    # Initialize session state for image modal
    image_modal_key = f"image_modal_{invoice_detail.get('id', 'default')}"
    if image_modal_key not in st.session_state:
        st.session_state[image_modal_key] = False
    
    # Render based on file type
    if file_type in ["jpg", "jpeg", "png", "gif", "webp"]:
        _render_image_preview(resolved_path, file_name, invoice_detail, image_modal_key, col_width)
    elif file_type == "pdf":
        _render_pdf_preview(resolved_path, file_name, invoice_detail)
    elif file_type in ["csv", "xlsx", "xls"]:
        _render_spreadsheet_preview(resolved_path, file_name, file_type, invoice_detail)
    else:
        st.info(f"📄 {file_type.upper()} File")
        st.caption(f"Path: `{resolved_path}`")
    
    # Show file location info
    if resolved["location"] == "encrypted":
        st.caption(f"📍 File location: Encrypted storage")


def _render_image_preview(
    file_path: Path,
    file_name: str,
    invoice_detail: Dict[str, Any],
    modal_key: str,
    col_width: int
):
    """Render image preview with full-size modal.
    
    Args:
        file_path: Path to the image file
        file_name: Original file name
        invoice_detail: Invoice detail dictionary
        modal_key: Session state key for modal
        col_width: Width of the preview column
    """
    # Display thumbnail in a container
    with st.container():
        # Thumbnail with click to view button
        col_thumb1, col_thumb2 = st.columns([3, 1])
        with col_thumb1:
            st.image(
                str(file_path),
                width=min(col_width - 100, 250),  # Responsive thumbnail size
                caption=file_name,
            )
        with col_thumb2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            if st.button("🔍 Full Size", key=f"view_full_{invoice_detail.get('id', 'default')}"):
                st.session_state[modal_key] = True
                st.rerun()
    
    # Full-size image modal
    if st.session_state[modal_key]:
        st.markdown("---")
        with st.container(border=True):
            # Modal header with close button
            col_modal1, col_modal2 = st.columns([10, 1])
            with col_modal1:
                st.markdown(f"### 🔍 Full Size Image: {file_name}")
            with col_modal2:
                if st.button("✕ Close", key=f"close_modal_{invoice_detail.get('id', 'default')}"):
                    st.session_state[modal_key] = False
                    st.rerun()
            
            # Full-size image
            st.image(
                str(file_path),
                caption=file_name,
                width="stretch",
            )
        st.markdown("---")


def _render_pdf_preview(file_path: Path, file_name: str, invoice_detail: Dict[str, Any]):
    """Render PDF preview using base64 embedding.
    
    Args:
        file_path: Path to the PDF file
        file_name: Original file name
        invoice_detail: Invoice detail dictionary
    """
    try:
        # Read PDF file
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Convert to base64
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Embed PDF using iframe
        pdf_display = f'''
        <div style="height:400px; overflow:auto;">
            <embed
                src="data:application/pdf;base64,{base64_pdf}"
                type="application/pdf"
                width="100%"
                height="400px"
            />
        </div>
        '''
        st.markdown(pdf_display, unsafe_allow_html=True)
        st.caption(f"📄 {file_name}")
        
        # Download button
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
            key=f"download_pdf_{invoice_detail.get('id', 'default')}"
        )
    
    except Exception as e:
        logger.error("Failed to render PDF preview", error=str(e), file_path=str(file_path))
        st.error(f"Failed to load PDF: {str(e)}")
        st.caption(f"Path: `{file_path}`")


def _render_spreadsheet_preview(
    file_path: Path,
    file_name: str,
    file_type: str,
    invoice_detail: Dict[str, Any]
):
    """Render CSV/Excel spreadsheet preview.
    
    Args:
        file_path: Path to the spreadsheet file
        file_name: Original file name
        file_type: File type (csv, xlsx, xls)
        invoice_detail: Invoice detail dictionary
    """
    try:
        # Read file based on type
        if file_type == "csv":
            df = pd.read_csv(file_path)
        elif file_type in ["xlsx", "xls"]:
            df = pd.read_excel(file_path, engine="openpyxl" if file_type == "xlsx" else "xlrd")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Display basic info
        st.caption(f"📊 {file_name}")
        st.caption(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
        
        # Show preview (first 50 rows)
        with st.expander("📋 View Data Preview", expanded=True):
            display_rows = min(50, len(df))
            st.dataframe(
                df.head(display_rows),
                width="stretch",
                height=min(400, 35 * display_rows + 38)  # Dynamic height
            )
            
            if len(df) > display_rows:
                st.caption(f"Showing first {display_rows} of {len(df)} rows")
        
        # Show column info
        with st.expander("ℹ️ Column Information"):
            col_info = pd.DataFrame({
                "Column": df.columns,
                "Type": df.dtypes.astype(str),
                "Non-Null Count": df.count(),
                "Null Count": df.isnull().sum()
            })
            st.dataframe(col_info, width="stretch", hide_index=True)
        
        # Download button for processed CSV
        csv_data = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {file_type.upper()}",
            data=csv_data,
            file_name=file_name,
            mime="text/csv",
            key=f"download_{file_type}_{invoice_detail.get('id', 'default')}"
        )
    
    except Exception as e:
        logger.error(
            "Failed to render spreadsheet preview",
            error=str(e),
            file_path=str(file_path),
            file_type=file_type
        )
        st.error(f"Failed to load {file_type.upper()}: {str(e)}")
        st.caption(f"Path: `{file_path}`")


def render_extracted_data_with_confidence(extracted_data: Dict[str, Any]):
    """Render extracted data fields with confidence scores.
    
    Args:
        extracted_data: Extracted data dictionary with confidence fields
    """
    # Basic Information with confidence
    st.subheader("📊 Extracted Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vendor = extracted_data.get("vendor_name")
        vendor_conf = extracted_data.get("vendor_name_confidence")
        _render_field_with_confidence("Vendor", vendor, vendor_conf)
    
    with col2:
        inv_num = extracted_data.get("invoice_number")
        inv_num_conf = extracted_data.get("invoice_number_confidence")
        _render_field_with_confidence("Invoice Number", inv_num, inv_num_conf)
    
    with col3:
        inv_date = extracted_data.get("invoice_date")
        inv_date_conf = extracted_data.get("invoice_date_confidence")
        date_str = str(inv_date) if inv_date else None
        _render_field_with_confidence("Invoice Date", date_str, inv_date_conf)
    
    # Financial Information with confidence
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = extracted_data.get("total_amount")
        total_conf = extracted_data.get("total_amount_confidence")
        total_str = f"${total:,.2f}" if total is not None else None
        _render_field_with_confidence("Total Amount", total_str, total_conf)
    
    with col2:
        subtotal = extracted_data.get("subtotal")
        subtotal_conf = extracted_data.get("subtotal_confidence")
        subtotal_str = f"${subtotal:,.2f}" if subtotal is not None else None
        _render_field_with_confidence("Subtotal", subtotal_str, subtotal_conf)
    
    with col3:
        tax = extracted_data.get("tax_amount")
        tax_conf = extracted_data.get("tax_amount_confidence")
        tax_str = f"${tax:,.2f}" if tax is not None else None
        _render_field_with_confidence("Tax Amount", tax_str, tax_conf)
    
    with col4:
        currency = extracted_data.get("currency")
        currency_conf = extracted_data.get("currency_confidence")
        _render_field_with_confidence("Currency", currency, currency_conf)


def _render_field_with_confidence(
    label: str,
    value: Optional[str],
    confidence: Optional[float]
):
    """Render a field with its confidence score.
    
    Args:
        label: Field label
        value: Field value
        confidence: Confidence score (0-1)
    """
    # Display value
    display_value = value if value else "—"
    
    # Confidence badge
    if confidence is not None:
        conf_float = float(confidence)
        if conf_float >= 0.8:
            conf_color = "green"
            conf_emoji = "🟢"
        elif conf_float >= 0.6:
            conf_color = "orange"
            conf_emoji = "🟡"
        else:
            conf_color = "red"
            conf_emoji = "🔴"
        
        st.markdown(f"**{label}**")
        st.markdown(f"{display_value}")
        st.caption(f"{conf_emoji} Confidence: {conf_float:.0%}")
    else:
        st.metric(label, display_value)

