# Quickstart: Dataset Upload UI

**Created**: 2026-01-05  
**Purpose**: Get started with implementing the dataset upload UI feature

## Overview

This feature adds file upload functionality to the Streamlit dashboard, allowing users to upload invoice files directly through the web interface instead of manually placing files in the `data/` folder.

## Implementation Steps

### 1. Database Migration

Create and run the migration to add `upload_metadata` field:

```bash
# Create migration
alembic revision -m "add_upload_metadata"

# Edit the migration file to add upload_metadata JSONB field and indexes
# See data-model.md for schema details

# Run migration
alembic upgrade head
```

**Migration File**: `alembic/versions/003_add_upload_metadata.py`

**Key Changes**:
- Add `upload_metadata` JSONB column to `invoices` table
- Add GIN index on `upload_metadata`
- Add indexes on `upload_metadata->>'subfolder'` and `upload_metadata->>'group'`

### 2. Update Invoice Model

**File**: `core/models.py`

Add to `Invoice` class:

```python
upload_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

Update table args to include new indexes (handled in migration).

### 3. Create Upload API Endpoint

**File**: `interface/api/routes/uploads.py` (new file)

**Key Components**:
- `POST /api/v1/uploads`: Handle multipart file uploads
- Validate file types and sizes
- Save files to `data/uploads/` (or specified subfolder)
- Create invoice records with metadata
- Trigger processing via existing `process_invoice_file` function
- Return upload status and invoice IDs

**Dependencies**:
- `fastapi.UploadFile` for file handling
- `python-multipart` (already in dependencies)
- Existing `process_invoice_file` from `ingestion.orchestrator`

### 4. Update API Schemas

**File**: `interface/api/schemas.py`

Add new schemas:
- `UploadResponse`: Response for upload endpoint
- `UploadItem`: Individual file upload result
- `UploadStatusResponse`: Status check response
- `UploadMetadata`: Metadata structure

### 5. Create Upload UI Component

**File**: `interface/dashboard/components/upload.py` (new file)

**Key Features**:
- `st.file_uploader` with `accept_multiple_files=True`
- File type filtering (PDF, Excel, CSV, images)
- Progress indicators using `st.progress`
- Status display for each file
- Duplicate detection warning
- Retry functionality for failed uploads
- Summary display (success/failed/skipped counts)

**UI Flow**:
1. User selects files (drag-and-drop or file picker)
2. Files validated client-side (type, size)
3. Upload to API endpoint
4. Show progress for each file
5. Display results (success/failed/skipped)
6. Link to processed invoices

### 6. Integrate into Dashboard

**File**: `interface/dashboard/app.py`

**Changes**:
- Add new tab: `tab3 = st.tabs(["Invoice List", "Invoice Detail", "Upload Files"])`
- Import upload component
- Add upload tab content

**Example**:
```python
tab1, tab2, tab3 = st.tabs(["Invoice List", "Invoice Detail", "Upload Files"])

with tab3:
    from interface.dashboard.components.upload import render_upload_ui
    render_upload_ui()
```

### 7. Update Invoice Detail View

**File**: `interface/dashboard/app.py` (in `display_invoice_detail` function)

**Changes**:
- Display `upload_metadata` in detail view
- Show subfolder, group, category if present
- Indicate upload source (web-ui vs data-folder)

**Example**:
```python
if invoice.upload_metadata:
    st.subheader("Upload Information")
    metadata = invoice.upload_metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Source Folder", metadata.get("subfolder", "N/A"))
    with col2:
        st.metric("Group", metadata.get("group", "N/A"))
    with col3:
        st.metric("Category", metadata.get("category", "N/A"))
    st.caption(f"Upload Source: {metadata.get('upload_source', 'N/A')}")
```

### 8. Update Orchestrator

**File**: `ingestion/orchestrator.py`

**Changes**:
- Update `process_invoice_file` to accept optional metadata parameter
- Set `upload_metadata` when creating invoice record if provided
- For files from data/ folder, set metadata with subfolder and upload_source="data-folder"

### 9. Register API Route

**File**: `interface/api/main.py`

**Changes**:
- Import upload router: `from interface.api.routes import uploads`
- Register router: `app.include_router(uploads.router)`

### 10. Testing

**Unit Tests**: `tests/unit/test_upload_component.py`
- Test file validation
- Test duplicate detection
- Test progress display
- Test error handling

**Integration Tests**: `tests/integration/test_upload_api.py`
- Test file upload endpoint
- Test file storage
- Test processing integration
- Test metadata storage
- Test error responses

**Test Commands**:
```bash
# Run all tests
pytest

# Run upload tests only
pytest tests/unit/test_upload_component.py tests/integration/test_upload_api.py

# Run with coverage
pytest --cov=interface --cov=core --cov-report=html
```

## Development Workflow

1. **Start API server**:
   ```bash
   uvicorn interface.api.main:app --reload
   ```

2. **Start Streamlit dashboard**:
   ```bash
   streamlit run interface/dashboard/app.py
   ```

3. **Test upload flow**:
   - Navigate to dashboard: http://localhost:${UI_PORT:-8501}
   - Click "Upload Files" tab
   - Select test invoice files
   - Verify upload and processing
   - Check invoice detail view for metadata

## Key Files Summary

| File | Purpose | Status |
|------|---------|--------|
| `alembic/versions/003_add_upload_metadata.py` | Database migration | New |
| `core/models.py` | Add upload_metadata field | Update |
| `interface/api/routes/uploads.py` | Upload API endpoint | New |
| `interface/api/schemas.py` | Upload schemas | Update |
| `interface/dashboard/components/upload.py` | Upload UI component | New |
| `interface/dashboard/app.py` | Integrate upload tab | Update |
| `ingestion/orchestrator.py` | Support metadata in processing | Update |
| `interface/api/main.py` | Register upload route | Update |

## Common Issues

**Issue**: Files not saving to correct location
- **Solution**: Verify `data/uploads/` directory exists and is writable
- **Check**: File path construction in upload endpoint

**Issue**: Duplicate detection not working
- **Solution**: Verify file hash calculation matches existing logic
- **Check**: Hash comparison in upload endpoint

**Issue**: Processing not starting after upload
- **Solution**: Verify `process_invoice_file` is called after file save
- **Check**: Error handling in upload endpoint

**Issue**: Metadata not displaying in detail view
- **Solution**: Verify metadata is saved correctly in invoice record
- **Check**: JSONB field structure matches expected format

## Next Steps

After implementing the basic upload functionality:

1. Add filtering by subfolder/group/category in invoice list
2. Add batch management UI (view/edit groups)
3. Add upload history/audit log
4. Add file preview before upload
5. Add bulk operations on uploaded files

## References

- [Specification](spec.md)
- [Data Model](data-model.md)
- [Research](research.md)
- [API Contract](contracts/openapi.yaml)

