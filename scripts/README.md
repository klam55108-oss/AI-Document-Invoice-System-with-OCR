# Utility Scripts

This directory contains various utility scripts for setting up the environment, processing invoices, and maintaining the database.

## � Quick Reference

| Use Case | Script | Example command |
| :--- | :--- | :--- |
| **Process local files** | `process_invoices.py` | `python3 scripts/process_invoices.py --dir data/` |
| **Inspect a specific invoice** | `inspect_invoice.py` | `python3 scripts/inspect_invoice.py <ID>` |
| **List recent failed extractions** | `inspect_invoice.py` | `python3 scripts/inspect_invoice.py --failed` |
| **Check status of a batch job** | `inspect_invoice.py` | `python3 scripts/inspect_invoice.py --job <ID>` |
| **Test OCR/PDF on a file** | `debug_ocr.py` | `python3 scripts/debug_ocr.py <file>` |
| **Query/Chat with your data** | `debug_chatbot.py` | `python3 scripts/debug_chatbot.py "query"` |
| **Reset or clean up data** | `cleanup_data.py` | `python3 scripts/cleanup_data.py --all` |
| **Start/Restart API server** | `restart_api.sh` | `./scripts/restart_api.sh` |
| **Initial environment setup** | `setup.sh` | `./scripts/setup.sh` |

---

## �🚀 Processing Scripts

### process_invoices.py
The primary script for batch processing invoices. It walks through a directory and sends files to the AI-eInvoicing engine for extraction and validation.

**Usage:**
```bash
# Process all files in data/
python3 scripts/process_invoices.py

# Specify category and group
python3 scripts/process_invoices.py --category "Invoice" --group "Vendor_X" --dir data/vendor_x
```

---

## 🔍 Debugging & Inspection

### inspect_invoice.py
**The all-in-one tool for checking an invoice's lifecycle.** Shows processing status, error messages, extracted AI data, and validation rule results.

**Usage:**
```bash
# Inspect the most recently processed invoice
python3 scripts/inspect_invoice.py

# List recent failed invoices
python3 scripts/inspect_invoice.py --failed

# List all invoices for a specific batch job
python3 scripts/inspect_invoice.py --job <job_id>

# Inspect by specific UUID or partial filename
python3 scripts/inspect_invoice.py 550e8400-e29b-41d4-a716-446655440000
python3 scripts/inspect_invoice.py "grok/1.jpg"
```

### debug_ocr.py
Consolidated tool for OCR testing and diagnostics. Supports image and PDF files.

**Usage:**
```bash
# Basic diagnostic (extract text and check key fields)
python3 scripts/debug_ocr.py data/samples/invoice.png

# Show full extracted text
python3 scripts/debug_ocr.py data/samples/invoice.png --raw

# Dump raw PaddleOCR structure for debugging
python3 scripts/debug_ocr.py data/samples/invoice.png --paddle-debug
```

### debug_chatbot.py
Diagnoses data availability for the chatbot and allows testing direct queries against the engine.

---

## 🧹 Maintenance & Cleanup

### cleanup_data.py
**Unified tool for data management.** Replace individual cleanup/reset scripts.

**Usage:**
```bash
# Show what would be deleted (safe)
python3 scripts/cleanup_data.py --all --dry-run

# Clean up only invoice records
python3 scripts/cleanup_data.py --invoices

# Clean up only vector embeddings
python3 scripts/cleanup_data.py --vectors

# Comprehensive reset (database + files)
python3 scripts/cleanup_data.py --all --storage
```

### test_db_connection.py
Tests database connection and schema health.

---

## 🛠 Setup & Infrastructure

### setup.sh
Initializes the environment, installs dependencies, and starts Docker services.

### setup_queue.sh
Sets up the `pgqueuer` schema for background job processing.

### start_safe_api.sh
Starts the API server in "Safe Mode" (single worker, no reload) optimized for stable batch processing.

### restart_api.sh
Quick helper to find and restart the FastAPI server.

---

> [!IMPORTANT]
> - Ensure the FastAPI server is running before using `process_invoices.py`.
> - Cleanup scripts are destructive; always use `--dry-run` first.
> - OCR processing may take 30-180 seconds for first-time requests due to model loading.
