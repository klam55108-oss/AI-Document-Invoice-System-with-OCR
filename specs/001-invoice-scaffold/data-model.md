# Data Model

**Created**: 2024-12-19  
**Purpose**: Define database entities, relationships, validation rules, and state transitions

## Entity Relationship Diagram

```
┌─────────────────┐
│   ProcessingJob │
│  (Job Tracking) │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│     Invoice     │──────│  ExtractedData   │
│  (Document)    │ 1:1  │  (Structured)    │
└────────┬────────┘      └──────────────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│ ValidationResult│
│  (Rule Checks)  │
└─────────────────┘
```

## Core Entities

### Invoice

**Purpose**: Represents a processed invoice document with version tracking

**Table**: `invoices`

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier (database-generated) |
| `storage_path` | VARCHAR(512) | NOT NULL | Original file path in data/ directory |
| `file_name` | VARCHAR(256) | NOT NULL | Original filename |
| `category` | VARCHAR(100) | NULL, INDEX | Logical category (e.g. Invoice, Receipt) |
| `group` | VARCHAR(100) | NULL, INDEX | Logical group/source (e.g. grok, jimeng) |
| `job_id` | UUID | NULL, INDEX | Batch/Job identifier |
| `file_hash` | VARCHAR(64) | NOT NULL, INDEX | SHA-256 hash of file content |
| `file_size` | BIGINT | NOT NULL | File size in bytes |
| `file_type` | VARCHAR(10) | NOT NULL | File extension (pdf, xlsx, csv, jpg, png, etc.) |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Version number (increments on reprocessing) |
| `processing_status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Status: pending, queued, processing, completed, failed |
| `encrypted_file_path` | VARCHAR(512) | NULL | Path to encrypted file (if encryption enabled) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Processing start timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |
| `processed_at` | TIMESTAMP | NULL | Completion timestamp |
| `error_message` | TEXT | NULL | Error details if processing failed |
| `upload_metadata` | JSONB | NULL | Metadata about file upload |

**Indexes**:
- `idx_invoices_file_hash` on `file_hash` (for duplicate detection)
- `idx_invoices_status` on `processing_status` (for job queries)
- `idx_invoices_created_at` on `created_at` (for sorting)

**Validation Rules**:
- `file_hash` must be valid SHA-256 hex string (64 characters)
- `file_type` must be one of: pdf, xlsx, csv, xls, jpg, jpeg, png
- `processing_status` must be one of: pending, queued, processing, completed, failed
- `version` must be >= 1

**State Transitions**:
```
pending → queued → processing → completed
                              ↓
                            failed
```

### ExtractedData

**Purpose**: Structured representation of invoice information extracted from documents

**Table**: `extracted_data`

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `invoice_id` | UUID | FOREIGN KEY, NOT NULL, UNIQUE | Reference to invoices.id (1:1 relationship) |
| `vendor_name` | VARCHAR(256) | NULL | Extracted vendor/supplier name |
| `invoice_number` | VARCHAR(100) | NULL | Invoice number from document |
| `invoice_date` | DATE | NULL | Invoice date |
| `due_date` | DATE | NULL | Payment due date (if present) |
| `subtotal` | DECIMAL(15,2) | NULL | Subtotal amount before tax |
| `tax_amount` | DECIMAL(15,2) | NULL | Tax amount |
| `tax_rate` | DECIMAL(5,4) | NULL | Tax rate percentage (e.g., 0.10 for 10%) |
| `total_amount` | DECIMAL(15,2) | NULL | Total amount including tax |
| `currency` | VARCHAR(3) | NULL, DEFAULT 'USD' | Currency code (ISO 4217) |
| `line_items` | JSONB | NULL | Array of line items (if extracted) |
| `raw_text` | TEXT | NULL | Full extracted text for future RAG indexing |
| `extraction_confidence` | DECIMAL(3,2) | NULL | Confidence score (0.00-1.00) |
| `extracted_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Extraction timestamp |

**Indexes**:
- `idx_extracted_data_invoice_id` on `invoice_id` (foreign key)
- `idx_extracted_data_vendor` on `vendor_name` (for filtering)
- `idx_extracted_data_date` on `invoice_date` (for date range queries)

**Validation Rules**:
- `subtotal`, `tax_amount`, `total_amount` must be >= 0 if not NULL
- `tax_rate` must be between 0 and 1 if not NULL
- `currency` must be valid ISO 4217 code if not NULL
- `extraction_confidence` must be between 0.00 and 1.00 if not NULL
- Mathematical validation: `subtotal + tax_amount ≈ total_amount` (within tolerance)

**Line Items JSONB Structure**:
```json
[
  {
    "description": "Product or service description",
    "quantity": 1.0,
    "unit_price": 100.00,
    "amount": 100.00
  }
]
```

### ValidationResult

**Purpose**: Records the outcome of validation checks performed on invoice data

**Table**: `validation_results`

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `invoice_id` | UUID | FOREIGN KEY, NOT NULL | Reference to invoices.id (1:N relationship) |
| `rule_name` | VARCHAR(100) | NOT NULL | Validation rule identifier (e.g., 'math_check_subtotal_tax') |
| `rule_description` | TEXT | NULL | Human-readable rule description |
| `status` | VARCHAR(20) | NOT NULL | Validation status: passed, failed, warning |
| `expected_value` | DECIMAL(15,2) | NULL | Expected calculated value |
| `actual_value` | DECIMAL(15,2) | NULL | Actual value from invoice |
| `tolerance` | DECIMAL(10,4) | NULL | Allowed tolerance for comparison |
| `error_message` | TEXT | NULL | Error details if validation failed |
| `validated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Validation timestamp |

**Indexes**:
- `idx_validation_results_invoice_id` on `invoice_id` (foreign key)
- `idx_validation_results_status` on `status` (for filtering failed validations)
- `idx_validation_results_rule` on `rule_name` (for rule-specific queries)

**Validation Rules**:
- `status` must be one of: passed, failed, warning
- `rule_name` must be non-empty and follow naming convention: `{category}_{specific_check}`

**Predefined Validation Rules** (Scaffold Phase):
1. **math_check_subtotal_tax**: Validates `subtotal + tax_amount = total_amount` (within tolerance)
   - Tolerance: 0.01 (1 cent)
   - Status: failed if difference exceeds tolerance

### ProcessingJob

**Purpose**: Tracks the status of invoice processing tasks, including I/O and CPU-bound operations

**Table**: `processing_jobs`

**Attributes**:

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier |
| `invoice_id` | UUID | FOREIGN KEY, NOT NULL | Reference to invoices.id |
| `job_type` | VARCHAR(50) | NOT NULL | Job type: file_ingestion, ocr_processing, data_extraction, validation |
| `execution_type` | VARCHAR(20) | NOT NULL | Execution type: async_coroutine, cpu_process |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Status: pending, queued, processing, completed, failed |
| `worker_id` | VARCHAR(100) | NULL | Worker/process identifier |
| `started_at` | TIMESTAMP | NULL | Job start timestamp |
| `completed_at` | TIMESTAMP | NULL | Job completion timestamp |
| `error_message` | TEXT | NULL | Error details if job failed |
| `error_traceback` | TEXT | NULL | Full error traceback for debugging |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | Number of retry attempts (scaffold: no retries) |
| `job_metadata` | JSONB | NULL | Additional job metadata (file size, processing time, etc.) |

**Indexes**:
- `idx_processing_jobs_invoice_id` on `invoice_id` (foreign key)
- `idx_processing_jobs_status` on `status` (for job queue queries)
- `idx_processing_jobs_type` on `job_type` (for filtering by job type)

**Validation Rules**:
- `job_type` must be one of: file_ingestion, ocr_processing, data_extraction, validation
- `execution_type` must be one of: async_coroutine, cpu_process
- `status` must be one of: pending, queued, processing, completed, failed
- `retry_count` must be >= 0

**State Transitions**:
```
pending → queued → processing → completed
                              ↓
                            failed
```

## Relationships

1. **Invoice → ExtractedData**: One-to-One
   - One invoice has exactly one extracted data record
   - ExtractedData.invoice_id references Invoice.id (UNIQUE constraint)

2. **Invoice → ValidationResult**: One-to-Many
   - One invoice can have multiple validation results (one per rule)
   - ValidationResult.invoice_id references Invoice.id

3. **Invoice → ProcessingJob**: One-to-Many
   - One invoice can have multiple processing jobs (different stages)
   - ProcessingJob.invoice_id references Invoice.id

## Database Schema Setup

### PostgreSQL Extensions

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector for vector storage
CREATE EXTENSION IF NOT EXISTS pgqueuer;  -- Job queue management
```

### Migration Strategy

- Use Alembic for database migrations
- Initial migration creates all tables, indexes, and constraints
- Future migrations for schema changes (versioning, new fields)

### Vector Storage (Future RAG)

The `extracted_data.raw_text` field will be indexed as vectors for RAG:
- Use `pgvector` extension
- Create separate `invoice_embeddings` table (deferred to later phase)
- Embedding dimension: 1536 (OpenAI) or 384 (smaller models)

## Data Integrity Constraints

1. **Referential Integrity**: All foreign keys have CASCADE DELETE (invoice deletion removes related records)
2. **Uniqueness**: File hash + version combination should be unique (prevent duplicate processing)
3. **Check Constraints**: Amounts must be non-negative, dates must be valid
4. **Not Null**: Critical fields (id, invoice_id, status, timestamps) cannot be NULL

## Indexing Strategy

**Primary Indexes** (for lookups):
- All primary keys (UUID)
- Foreign keys (for joins)
- Status fields (for filtering)

**Composite Indexes** (for queries):
- `(file_hash, version)` for duplicate detection
- `(processing_status, created_at)` for job queue queries
- `(vendor_name, invoice_date)` for dashboard filtering

## Data Volume Assumptions

**MVP/Scaffold Phase**:
- Expected invoices: 100-1,000 documents
- Average file size: 1-5 MB
- Storage: Local filesystem (encrypted)
- Database size: <100 MB

**Future Scaling**:
- Vector embeddings: ~1 KB per document
- Index size: ~10% of data size
- Partitioning strategy: By date or vendor (if needed)

