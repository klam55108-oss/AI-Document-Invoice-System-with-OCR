# Utility Scripts

This directory contains various utility scripts for setting up the environment, processing invoices, and maintaining the database.

## Processing Scripts

### [process_invoices.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/process_invoices.py)
The primary script for batch processing invoices. It sends files to the API for OCR extraction and validation.

**Usage:**
```bash
# Process all files in data/
python3 scripts/process_invoices.py

# Process a specific directory
python3 scripts/process_invoices.py --dir data/jimeng

# Search recursively and use a glob pattern
python3 scripts/process_invoices.py --dir data/ --pattern "*.png" --recursive

# Force reprocessing of already indexed files
python3 scripts/process_invoices.py --force
```

**Arguments:**
- `--dir`, `-d`: Directory to search (default: `data/`)
- `--pattern`, `-p`: Glob pattern (default: `*`)
- `--recursive`, `-r`: Search subdirectories
- `--force`, `-f`: Force re-processing
- `--api-url`: API base URL (default: `http://localhost:8000`)

---

## Maintenance & Cleanup

### [reset_all_data.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/reset_all_data.py)
**Comprehensive script to reset all data: pgvector embeddings, extracted_data, and optionally persistent storage files.**

This is the recommended script for a complete reset. It handles both `cleanup_vectors.py` and `cleanup_invoices.py` in the correct order.

**Usage:**
```bash
# Dry run to see what would be deleted
python3 scripts/reset_all_data.py --dry-run

# Reset database only (pgvector + extracted_data)
python3 scripts/reset_all_data.py

# Reset database + persistent storage files
python3 scripts/reset_all_data.py --cleanup-files

# Selective cleanup (only vectors, keep extracted_data)
python3 scripts/reset_all_data.py --no-extracted

# Selective cleanup (only extracted_data, keep vectors)
python3 scripts/reset_all_data.py --no-vectors
```

**What it cleans:**
- ✅ pgvector embeddings (`invoice_embeddings` table)
- ✅ Invoice tables (`invoices`, `extracted_data`, `validation_results`, `processing_jobs`)
- ✅ Optional: Persistent storage files in `data/` directory (with `--cleanup-files`)

---

### [cleanup_vectors.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/cleanup_vectors.py)
**Cleans up pgvector embeddings and vector-related tables only.**

Deletes:
- `invoice_embeddings` table (pgvector embeddings)
- Any tables with `vector` type columns
- LlamaIndex tables (`data_*`, `vector_store_*`, `llama_*`)

**Does NOT touch:**
- Invoice tables (`invoices`, `extracted_data`, etc.)
- Validation results
- Processing jobs

**Usage:**
```bash
# List vector tables without deleting
python3 scripts/cleanup_vectors.py --list-only

# Clear all vector data
python3 scripts/cleanup_vectors.py
```

**When to use:**
- When you want to reset embeddings but keep invoice data
- When you need to re-embed all invoices with a new model

---

### [cleanup_invoices.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/cleanup_invoices.py)
**Cleans up invoice-related relational data only.**

Deletes:
- `invoices` table
- `extracted_data` table
- `validation_results` table
- `processing_jobs` table

**Does NOT touch:**
- pgvector/embeddings tables
- Vector data

**Usage:**
```bash
# Dry run to see what would be deleted
python3 scripts/cleanup_invoices.py --dry-run

# Delete all invoice data
python3 scripts/cleanup_invoices.py

# Delete invoices matching a storage path pattern
python3 scripts/cleanup_invoices.py --file-path-filter "jimeng/"
```

**When to use:**
- When you want to reset invoice data but keep embeddings
- When you need to clean up specific invoices by storage path pattern

---

### Which Script to Use?

| Scenario | Recommended Script |
|----------|-------------------|
| **Complete reset** (everything) | `reset_all_data.py` |
| **Reset embeddings only** (keep invoices) | `cleanup_vectors.py` |
| **Reset invoices only** (keep embeddings) | `cleanup_invoices.py` |
| **Selective cleanup** (specific invoices) | `cleanup_invoices.py --file-path-filter` |

### Recommended Order (if running separately)

If you need to run `cleanup_vectors.py` and `cleanup_invoices.py` separately:

1. **First**: Run `cleanup_vectors.py` (clean embeddings)
2. **Then**: Run `cleanup_invoices.py` (clean invoice data)

**Why this order?**
- Embeddings reference invoices (via `invoice_id`), so cleaning vectors first avoids orphaned references
- Vectors are typically larger and slower to delete
- Logical flow: remove derived data (embeddings) before source data (invoices)

**However**, the order doesn't matter for data integrity - both scripts handle foreign key constraints correctly. For convenience, use `reset_all_data.py` which does both in the correct order automatically.

---

## Setup & Verification

### [setup.sh](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/setup.sh)
Initializes the development environment, creates a virtualenv, installs dependencies, and starts the database via Docker.

**Usage:**
```bash
./scripts/setup.sh
```

### [setup_queue.sh](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/setup_queue.sh)
Installs the `pgqueuer` schema into the database for background job processing.

**Usage:**
```bash
./scripts/setup_queue.sh
```

### [test_db_connection.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/test_db_connection.py)
Tests database connection and schema health. Verifies all required tables exist and checks schema version.

**Usage:**
```bash
python scripts/test_db_connection.py
```

### [test_ocr_safe.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/test_ocr_safe.py)
Safely tests OCR processing on an image file with proper timeouts and resource limits. Useful for debugging OCR issues.

**Usage:**
```bash
python scripts/test_ocr_safe.py data/grok/1.jpg
```

### [check_invoice_status.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/check_invoice_status.py)
Checks the processing status and error details for a specific invoice by ID.

**Usage:**
```bash
python scripts/check_invoice_status.py <invoice_id>
```

### [verify_docling.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/verify_docling.py)
A test script to verify that Docling PDF processing and LLM extraction are working correctly.

**Usage:**
```bash
python3 scripts/verify_docling.py
```

---

## Important Notices

> [!IMPORTANT]
> - Ensure the FastAPI server (`interface/api/main.py`) is running before using `process_invoices.py`.
> - The database must be accessible and migrated (`alembic upgrade head`) before running maintenance scripts.
> - Cleanup scripts are destructive; always use `--dry-run` or `--list-only` first if available.
> - OCR processing may take 30-180 seconds for first-time requests due to model loading.
> - Use `test_ocr_safe.py` to test OCR processing without risking system crashes.
