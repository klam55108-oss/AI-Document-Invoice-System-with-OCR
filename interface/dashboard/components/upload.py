"""Upload UI component for Streamlit dashboard."""

import io
from pathlib import Path

import httpx
import streamlit as st

from core.logging import get_logger

logger = get_logger(__name__)

# Supported file types for Streamlit file uploader
ACCEPTED_TYPES = [
    ".pdf",
    ".xlsx",
    ".xls",
    ".csv",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".avif",
]

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


def render_upload_ui(api_base_url: str = "http://127.0.0.1:8000") -> None:
    """Render the file upload UI component.

    Args:
        api_base_url: Base URL for the API server
    """
    st.header("📤 Upload Invoice Files")
    st.markdown("Upload invoice files directly through the web interface. Files will be automatically processed.")

    # Initialize session state for upload history
    if "upload_history" not in st.session_state:
        st.session_state.upload_history = []

    # File uploader
    uploaded_files = st.file_uploader(
        "Select invoice files to upload",
        type=[ext.lstrip(".") for ext in ACCEPTED_TYPES],
        accept_multiple_files=True,
        help="Supported formats: PDF, Excel (.xlsx, .xls), CSV, Images (.jpg, .jpeg, .png, .webp, .avif). Maximum file size: 50MB per file.",
    )

    if uploaded_files:
        # Metadata inputs
        with st.expander("Upload Options (Optional)", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                subfolder = st.text_input(
                    "Subfolder",
                    value="uploads",
                    help="Subfolder within data/ directory to store files",
                )
                group = st.text_input(
                    "Group/Batch",
                    help="Group identifier for organizing related uploads",
                )
            with col2:
                category = st.text_input(
                    "Category",
                    help="Category for organizing uploads (e.g., monthly-invoices)",
                )
                force_reprocess = st.checkbox(
                    "Force Reprocess",
                    value=False,
                    help="Reprocess files even if they already exist",
                )

        # Validate files before upload
        invalid_files = []
        for file in uploaded_files:
            if file.size > MAX_FILE_SIZE:
                invalid_files.append(f"{file.name} ({file.size / 1024 / 1024:.2f}MB exceeds 50MB limit)")

        if invalid_files:
            st.error("Some files are too large:")
            for msg in invalid_files:
                st.error(f"  - {msg}")

        # Upload button
        if st.button("Upload Files", type="primary", disabled=len(invalid_files) > 0):
            upload_files_to_api(
                uploaded_files,
                api_base_url,
                subfolder or "uploads",
                group,
                category,
                force_reprocess,
            )

    # Display upload history with status polling and retry
    if st.session_state.upload_history:
        st.divider()
        col_header1, col_header2 = st.columns([4, 1])
        with col_header1:
            st.subheader("Recent Uploads")
        with col_header2:
            # Check for processing items that need status updates
            processing_items = [
                item for item in st.session_state.upload_history
                if item.get("status") == "processing" and item.get("invoice_id")
            ]
            if processing_items:
                if st.button("🔄 Refresh Status", help="Check status of processing uploads"):
                    # Update status for processing items
                    updated = False
                    for item in processing_items:
                        if item.get("invoice_id"):
                            try:
                                with httpx.Client(timeout=10.0) as client:
                                    response = client.get(
                                        f"{api_base_url}/api/v1/uploads/{item['invoice_id']}/status"
                                    )
                                    if response.status_code == 200:
                                        status_data = response.json().get("data", {})
                                        new_status = status_data.get("processing_status", "processing")
                                        if item["status"] != new_status:
                                            item["status"] = new_status
                                            updated = True
                            except Exception:
                                pass  # Silently fail status checks
                    if updated:
                        st.rerun()
        
        for history_item in reversed(st.session_state.upload_history[-10:]):  # Show last 10
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.text(history_item["file_name"])
                    if history_item.get("error_message"):
                        st.caption(f"❌ {history_item['error_message']}")
                with col2:
                    status_color = {
                        "processing": "🟡",
                        "completed": "🟢",
                        "failed": "🔴",
                        "duplicate": "🟠",
                    }.get(history_item["status"], "⚪")
                    st.markdown(f"{status_color} {history_item['status']}")
                with col3:
                    if history_item.get("invoice_id"):
                        st.markdown(f"[View](/Invoice%20Detail?invoice_id={history_item['invoice_id']})")
                with col4:
                    # Retry button for failed uploads
                    if history_item.get("status") == "failed":
                        if st.button("🔄 Retry", key=f"retry_{history_item['file_name']}_{len(st.session_state.upload_history)}", width='stretch'):
                            st.info(f"To retry, please re-upload the file: {history_item['file_name']}")
                            st.caption("Note: Use the file uploader above to re-upload failed files.")


def upload_files_to_api(
    files: list,
    api_base_url: str,
    subfolder: str,
    group: str | None,
    category: str | None,
    force_reprocess: bool,
) -> None:
    """Upload files to the API endpoint.

    Args:
        files: List of uploaded file objects
        api_base_url: Base URL for the API server
        subfolder: Subfolder within data/ directory
        group: Group/batch identifier
        category: Category for organizing uploads
        force_reprocess: Force reprocessing even if file hash exists
    """
    if not files:
        st.warning("No files selected")
        return

    # Show file list with status indicators
    if len(files) > 1:
        st.subheader(f"Uploading {len(files)} files...")
        file_status_placeholders = {}
        for file in files:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(file.name)
                with col2:
                    file_status_placeholders[file.name] = st.empty()
                    file_status_placeholders[file.name].status("⏳ Queued")

    overall_progress = st.progress(0)
    status_text = st.empty()

    try:
        # Prepare multipart form data
        files_data = []
        for file in files:
            file.seek(0)  # Reset file pointer
            files_data.append(("files", (file.name, file.read(), file.type)))

        data = {
            "subfolder": subfolder,
            "force_reprocess": str(force_reprocess).lower(),
        }
        if group:
            data["group"] = group
        if category:
            data["category"] = category

        status_text.text("Uploading files...")
        overall_progress.progress(0.3)

        # Upload to API
        with httpx.Client(timeout=300.0) as client:  # 5 minute timeout for large files
            response = client.post(
                f"{api_base_url}/api/v1/uploads",
                files=files_data,
                data=data,
            )

        overall_progress.progress(0.7)

        if response.status_code == 202:
            result = response.json()
            upload_data = result.get("data", {})

            # Update file status indicators for multiple files
            if len(files) > 1:
                for upload_item in upload_data.get("uploads", []):
                    file_name = upload_item["file_name"]
                    status = upload_item["status"]
                    if file_name in file_status_placeholders:
                        status_emoji = {
                            "processing": "🟡 Processing",
                            "completed": "🟢 Completed",
                            "failed": "🔴 Failed",
                            "duplicate": "🟠 Duplicate",
                            "uploaded": "📤 Uploaded",
                        }.get(status, f"⚪ {status}")
                        file_status_placeholders[file_name].status(status_emoji)

            # Update session state with upload results
            for upload_item in upload_data.get("uploads", []):
                st.session_state.upload_history.append({
                    "file_name": upload_item["file_name"],
                    "status": upload_item["status"],
                    "invoice_id": upload_item.get("invoice_id"),
                    "error_message": upload_item.get("error_message"),
                })

            # Display results
            overall_progress.progress(1.0)
            status_text.empty()

            successful = upload_data.get("successful", 0)
            failed = upload_data.get("failed", 0)
            skipped = upload_data.get("skipped", 0)
            total = upload_data.get("total", len(files))

            # Summary display
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", total)
            with col2:
                st.metric("✅ Successful", successful, delta=None)
            with col3:
                st.metric("⚠️ Skipped", skipped, delta=None)
            with col4:
                st.metric("❌ Failed", failed, delta=None)

            if successful > 0:
                st.success(f"✅ {successful} file(s) uploaded and processing started")
            if skipped > 0:
                st.warning(f"⚠️ {skipped} file(s) skipped (duplicates)")
            if failed > 0:
                st.error(f"❌ {failed} file(s) failed to upload")

            # Show detailed results
            with st.expander("Upload Details", expanded=(failed > 0 or skipped > 0)):
                for upload_item in upload_data.get("uploads", []):
                    status_emoji = {
                        "processing": "🟡",
                        "completed": "🟢",
                        "failed": "🔴",
                        "duplicate": "🟠",
                        "uploaded": "📤",
                    }.get(upload_item["status"], "⚪")

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{upload_item['file_name']}** {status_emoji} {upload_item['status']}")
                    with col2:
                        if upload_item.get("file_size"):
                            size_mb = upload_item["file_size"] / 1024 / 1024
                            st.caption(f"{size_mb:.2f} MB")

                    if upload_item.get("error_message"):
                        st.caption(f"❌ Error: {upload_item['error_message']}")
                    if upload_item.get("invoice_id"):
                        st.caption(f"📄 Invoice ID: {upload_item['invoice_id']}")

        else:
            overall_progress.empty()
            error_data = response.json()
            error_detail = error_data.get("error", {})
            st.error(f"Upload failed: {error_detail.get('message', 'Unknown error')}")

    except httpx.RequestError as e:
        overall_progress.empty()
        status_text.empty()
        error_msg = f"Network error: {str(e)}. Please check that the API server is running."
        st.error(error_msg)
        logger.error("Upload network error", error=str(e), exc_info=True)
    except httpx.HTTPStatusError as e:
        overall_progress.empty()
        status_text.empty()
        error_msg = f"Server error: {e.response.status_code}. {e.response.text}"
        st.error(error_msg)
        logger.error("Upload HTTP error", status_code=e.response.status_code, error=str(e))
    except Exception as e:
        overall_progress.empty()
        status_text.empty()
        error_msg = f"Upload failed: {str(e)}"
        st.error(error_msg)
        logger.error("Upload error", error=str(e), exc_info=True)
