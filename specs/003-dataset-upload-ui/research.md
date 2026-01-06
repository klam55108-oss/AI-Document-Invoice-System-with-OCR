# Research: Dataset Upload UI

**Created**: 2026-01-05  
**Purpose**: Resolve technical decisions and best practices for file upload implementation

## Streamlit File Upload

**Decision**: Use `st.file_uploader` with `accept_multiple_files=True` for multiple file upload support

**Rationale**: 
- Streamlit's native `st.file_uploader` provides built-in file selection, drag-and-drop support, and file type filtering
- Supports multiple files natively with `accept_multiple_files=True`
- Returns `UploadedFile` objects that can be read directly into memory or saved to disk
- Integrates seamlessly with existing Streamlit dashboard architecture
- No additional dependencies required

**Alternatives considered**:
- Custom HTML/JavaScript upload component: Rejected due to complexity and need to maintain separate frontend code
- Third-party Streamlit components: Rejected to avoid additional dependencies when native component suffices

## File Upload API Endpoint

**Decision**: Create new `/api/v1/uploads` endpoint with `POST /api/v1/uploads` for file uploads

**Rationale**:
- Separates upload concerns from existing invoice processing endpoints
- Follows RESTful conventions for resource creation
- Allows for future expansion (e.g., upload status endpoints, batch management)
- Maintains consistency with existing API structure (`/api/v1/invoices`, `/api/v1/analytics`)

**Alternatives considered**:
- Extend existing `/api/v1/invoices/process` endpoint: Rejected because it expects file paths, not file uploads
- Single endpoint for both upload and processing: Rejected to maintain separation of concerns (upload vs. processing)

## File Storage Strategy

**Decision**: Store uploaded files in `data/uploads/` subdirectory with original filename preserved

**Rationale**:
- Maintains consistency with existing `data/` directory structure (e.g., `data/grok/`, `data/jimeng/`)
- Preserves original filenames for user recognition (FR-014)
- Uses relative paths from `data/` directory (consistent with existing `Invoice.file_path` field)
- Supports future organization by subdirectory (e.g., `data/uploads/2026/01/`)

**Alternatives considered**:
- Hash-based filenames: Rejected because users need to recognize files by original name
- Temporary location then move: Rejected as unnecessary complexity; direct storage is simpler

## Metadata Storage

**Decision**: Add `upload_metadata` JSONB field to `Invoice` model containing subfolder, group/batch/category

**Rationale**:
- JSONB provides flexibility for metadata structure without schema changes
- Allows querying and indexing on metadata fields in PostgreSQL
- Supports future metadata expansion without migrations
- Maintains backward compatibility (field is nullable)

**Metadata Structure**:
```json
{
  "subfolder": "uploads",
  "group": "batch-2026-01-05",
  "category": "monthly-invoices",
  "upload_source": "web-ui"
}
```

**Alternatives considered**:
- Separate `UploadMetadata` table: Rejected as over-engineering for simple key-value metadata
- Individual columns for each metadata field: Rejected due to lack of flexibility and need for frequent migrations

## Duplicate Detection

**Decision**: Check file hash before upload completes, show warning dialog in Streamlit UI

**Rationale**:
- File hash calculation is fast and can be done client-side or early in upload process
- Provides immediate feedback to user before processing begins
- Aligns with existing duplicate detection logic in `process_invoice_file`
- User confirmation prevents accidental reprocessing

**Alternatives considered**:
- Check after upload: Rejected because wastes bandwidth and storage for duplicates
- Automatic skip without notification: Rejected because user should be aware of duplicates

## Progress Tracking

**Decision**: Use Streamlit's session state and `st.progress` for upload progress, polling API for processing status

**Rationale**:
- Streamlit's native progress components provide good UX
- Session state maintains upload state across reruns
- API polling allows real-time status updates without WebSocket complexity
- Polling interval of 2-5 seconds balances responsiveness with server load

**Alternatives considered**:
- WebSocket for real-time updates: Rejected as unnecessary complexity for this use case
- Server-Sent Events (SSE): Rejected due to Streamlit's request-response model limitations

## Error Handling

**Decision**: Return structured error responses from API, display user-friendly messages in Streamlit

**Rationale**:
- Consistent with existing API error response format
- Streamlit can display errors clearly with `st.error()` and retry buttons
- Structured errors enable programmatic handling and logging
- User-friendly messages improve UX (FR-016)

**Error Response Format**:
```json
{
  "status": "error",
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds 50MB limit",
    "details": {"max_size": 52428800, "file_size": 60000000}
  }
}
```

## File Size Validation

**Decision**: Validate file size client-side (Streamlit) and server-side (API) with 50MB limit

**Rationale**:
- Client-side validation provides immediate feedback
- Server-side validation prevents bypassing client checks
- 50MB limit balances user needs with server resources (SC-008)
- Clear error messages guide users (FR-013)

## Integration with Processing Pipeline

**Decision**: After successful upload, automatically call existing `process_invoice_file` function

**Rationale**:
- Reuses existing, tested processing logic (FR-004)
- Maintains consistency with data/ folder workflow
- No duplicate code or logic divergence
- Automatic processing provides seamless user experience

**Flow**:
1. Upload file to `data/uploads/`
2. Save file metadata to database
3. Call `process_invoice_file` with uploaded file path
4. Update invoice record with processing results

