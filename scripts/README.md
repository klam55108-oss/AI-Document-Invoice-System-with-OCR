# Utility Scripts

This directory contains various utility scripts for setting up the environment, processing invoices, and maintaining the database.

## 🚀 Processing Scripts

### process_invoices.py
The primary script for batch processing invoices. It walks through a directory and sends files to the AI-eInvoicing engine for extraction and validation.

**Usage:**
```bash
# Process all files in data/
python3 scripts/process_invoices.py

# Process a specific subdirectory
python3 scripts/process_invoices.py --dir data/grok

# Search recursively for specific patterns
python3 scripts/process_invoices.py --dir data/ --pattern "*.png" --recursive

# Force reprocessing of already indexed files
python3 scripts/process_invoices.py --force
```

---

## 🔍 Debugging & Inspection

### inspect_invoice.py
**The all-in-one tool for checking an invoice's lifecycle.** Shows processing status, error messages, extracted AI data, line items, and validation rule results.

**Usage:**
```bash
# Inspect the most recently processed invoice
python3 scripts/inspect_invoice.py

# Inspect by specific UUID
python3 scripts/inspect_invoice.py 550e8400-e29b-41d4-a716-446655440000

# Inspect by partial filename search
python3 scripts/inspect_invoice.py "grok/1.jpg"
```

### debug_chatbot.py
Diagnoses data availability for the chatbot and allows testing direct queries against the engine.

**Usage:**
```bash
# Run data diagnosis only
python3 scripts/debug_chatbot.py

# Run diagnosis and test a specific query
python3 scripts/debug_chatbot.py "how many invoices are there from grok?"
```

### diagnose_ocr.py
Isolated test for the PaddleOCR engine. Prints raw text and diagnostic info to verify if the OCR can see specific keywords (like "销售方").

**Usage:**
```bash
python3 scripts/diagnose_ocr.py data/samples/invoice.png
```

---

## 🧹 Maintenance & Reset

### reset_all_data.py
**Comprehensive script to reset everything.** Cleans up vector embeddings, database records, and optionally persistent storage files.

**Usage:**
```bash
# Dry run (safe)
python3 scripts/reset_all_data.py --dry-run

# Full database reset
python3 scripts/reset_all_data.py

# Reset database + delete files in data/ directory
python3 scripts/reset_all_data.py --cleanup-files
```

### cleanup_vectors.py
Cleans up pgvector embeddings and LlamaIndex-related tables only. Useful if you want to re-train/re-embed without losing invoice metadata.

### cleanup_invoices.py
Cleans up relational invoice data while leaving embeddings intact.

---

## 🛠 Setup & Infrastructure

### setup.sh
Initializes the environment, installs dependencies, and starts Docker services.

### setup_queue.sh
Sets up the `pgqueuer` schema for background job processing.

### restart_api.sh
Quick helper to find and restart the FastAPI server.

### verify_docling.py
Verifies the PDF structure extraction pipeline using Docling.
