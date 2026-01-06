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

### [cleanup_invoices.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/cleanup_invoices.py)
Deletes invoice records, extracted data, and validation results from the database.

**Usage:**
```bash
# Dry run to see what would be deleted
python3 scripts/cleanup_invoices.py --dry-run

# Delete invoices matching a path pattern
python3 scripts/cleanup_invoices.py --file-path-filter "jimeng/"
```

### [cleanup_vectors.py](file:///Users/william.jiang/my-apps/ai-einvoicing/scripts/cleanup_vectors.py)
Cleans up all pgvector-related tables and LlamaIndex data.

**Usage:**
```bash
# List vector tables without deleting
python3 scripts/cleanup_vectors.py --list-only

# Clear all vector data
python3 scripts/cleanup_vectors.py
```

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
