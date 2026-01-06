# Data Model: Dataset Upload UI

**Created**: 2026-01-05  
**Purpose**: Define database schema changes and entity relationships for upload functionality

## Schema Changes

### Invoice Model Extension

**Table**: `invoices` (existing, extended)

**New Field**:

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `upload_metadata` | JSONB | NULL | Metadata about file upload including subfolder, group/batch/category, and upload source |

**Metadata Structure** (JSONB):

```json
{
  "subfolder": "uploads",
  "group": "batch-2026-01-05",
  "category": "monthly-invoices",
  "upload_source": "web-ui",
  "uploaded_at": "2026-01-05T10:30:00Z"
}
```

**Field Descriptions**:
- `subfolder`: String indicating the subdirectory within `data/` where the file is stored (e.g., "uploads", "grok", "jimeng")
- `group`: String for grouping related uploads (e.g., "batch-2026-01-05", "weekly-upload-2026-01")
- `category`: String for categorizing uploads (e.g., "monthly-invoices", "vendor-invoices", "expense-reports")
- `upload_source`: String indicating how the file was uploaded ("web-ui" for UI uploads, "data-folder" for files processed from data/ folder)
- `uploaded_at`: ISO 8601 timestamp of when the file was uploaded (for UI uploads)

**Indexes**:
- Add GIN index on `upload_metadata` for efficient JSONB queries:
  ```sql
  CREATE INDEX idx_invoices_upload_metadata ON invoices USING GIN (upload_metadata);
  ```
- Add index on `upload_metadata->>'subfolder'` for filtering by subfolder:
  ```sql
  CREATE INDEX idx_invoices_subfolder ON invoices ((upload_metadata->>'subfolder'));
  ```
- Add index on `upload_metadata->>'group'` for filtering by group:
  ```sql
  CREATE INDEX idx_invoices_upload_group ON invoices ((upload_metadata->>'group'));
  ```

**Migration**: `003_add_upload_metadata.py`

## Entity Relationships

### Invoice Entity (Extended)

**Relationships** (unchanged):
- `Invoice` → `ExtractedData` (1:1)
- `Invoice` → `ValidationResult` (1:N)
- `Invoice` → `ProcessingJob` (1:N)

**New Attributes**:
- `upload_metadata`: Optional JSONB field containing upload-related metadata

**Validation Rules**:
- `upload_metadata` is nullable (backward compatible with existing records)
- If `upload_metadata` is present, it must contain valid JSON structure
- `subfolder` must be a non-empty string if present
- `upload_source` must be either "web-ui" or "data-folder" if present

## Data Flow

### Upload Flow

1. **File Upload**:
   - User selects file(s) in Streamlit UI
   - File(s) uploaded to FastAPI endpoint
   - Files saved to `data/uploads/` (or specified subfolder)
   - File metadata calculated (hash, size, type)

2. **Invoice Record Creation**:
   - Create `Invoice` record with:
     - `storage_path`: Relative path from `data/` (e.g., "uploads/invoice-1.pdf")
     - `file_name`: Original filename
     - `file_hash`: SHA-256 hash
     - `file_size`: File size in bytes
     - `file_type`: File extension
     - `upload_metadata`: JSONB with subfolder, group, category, upload_source, uploaded_at
   - Status set to `PROCESSING`

3. **Processing**:
   - Call existing `process_invoice_file` function
   - Processing pipeline extracts data, validates, stores results
   - Status updated to `COMPLETED` or `FAILED`

### Metadata Usage

**Display in Detail View**:
- Show `upload_metadata.subfolder` as "Source Folder"
- Show `upload_metadata.group` as "Upload Group" (if present)
- Show `upload_metadata.category` as "Category" (if present)
- Show `upload_metadata.upload_source` to indicate upload method

**Filtering**:
- Filter invoices by subfolder (e.g., show only "uploads" folder)
- Filter invoices by group (e.g., show all invoices from "batch-2026-01-05")
- Filter invoices by category (e.g., show only "monthly-invoices")

**Query Examples**:

```sql
-- Find all invoices uploaded via web UI
SELECT * FROM invoices 
WHERE upload_metadata->>'upload_source' = 'web-ui';

-- Find all invoices in 'uploads' subfolder
SELECT * FROM invoices 
WHERE upload_metadata->>'subfolder' = 'uploads';

-- Find all invoices in a specific group
SELECT * FROM invoices 
WHERE upload_metadata->>'group' = 'batch-2026-01-05';
```

## Backward Compatibility

**Existing Records**:
- All existing `Invoice` records will have `upload_metadata = NULL`
- Existing records remain fully functional
- No data migration required for existing records

**Default Values**:
- For files processed from `data/` folder (existing workflow):
  ```json
  {
    "subfolder": "grok",  // or "jimeng", etc. based on actual subfolder
    "upload_source": "data-folder"
  }
  ```
- For files uploaded via UI:
  ```json
  {
    "subfolder": "uploads",
    "upload_source": "web-ui",
    "uploaded_at": "2026-01-05T10:30:00Z"
  }
  ```

## Constraints

**Database Constraints**:
- `upload_metadata` must be valid JSONB (enforced by PostgreSQL)
- If `upload_metadata` contains `subfolder`, it must be non-empty string
- If `upload_metadata` contains `upload_source`, it must be "web-ui" or "data-folder"

**Application-Level Validation**:
- Validate JSON structure before saving
- Ensure required fields are present when `upload_metadata` is not null
- Sanitize subfolder name to prevent path traversal (e.g., no ".." or "/")

