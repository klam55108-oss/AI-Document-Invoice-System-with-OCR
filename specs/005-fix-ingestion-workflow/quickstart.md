# Quickstart: Fix Ingestion Workflow

**Feature**: Fix Ingestion Workflow  
**Date**: 2025-01-27

## Prerequisites

- Python 3.12
- PostgreSQL database with pgvector extension
- All dependencies installed: `pip install -e ".[dev]"`
- Environment variables configured in `.env` file

## Step 1: Verify Database Schema

Check if database schema matches code models:

```bash
# Check current migration version
alembic current

# Upgrade to latest migration
alembic upgrade head

# Verify no errors
alembic check
```

## Step 2: Test Database Connection

Verify database connectivity:

```bash
# Use the test script
python scripts/test_db_connection.py
```

This script will:
- Test database connection
- Verify schema health
- Check for missing tables or columns
- Display current schema version

## Step 3: Test API Endpoint

Test the invoice processing endpoint:

```bash
# Start API server (in separate terminal)
uvicorn interface.api.main:app --reload

# Test POST endpoint
# IMPORTANT: First request may take 30-60 seconds as PaddleOCR loads models
# The initialization is now non-blocking and won't crash your system
# To suppress verbose output, redirect stderr: 2>/dev/null
# Add timeout to prevent hanging: --max-time 120

curl --max-time 120 -X POST "http://localhost:${API_PORT}/api/v1/invoices/process" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "grok/1.jpg",
    "force_reprocess": false
  }' 2>/dev/null

# Alternative: Test OCR directly (safer for first-time testing)
# python scripts/test_ocr_safe.py data/grok/1.jpg
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "invoice_id": "...",
    "job_id": "...",
    "status": "processing"
  }
}
```

## Step 4: Test Processing Script

Test the batch processing script:

```bash
# Process files in data/grok directory
python scripts/process_invoices.py --dir data/grok --recursive

# Check output for errors
```

Expected output:
```
📄 Found N invoice files to process
🌐 API endpoint: http://localhost:${API_PORT}
🔄 Force reprocess: False
🆔 Job ID: ...
------------------------------------------------------------
[1/N] Processing grok/1.jpg... ✅ Success (ID: ..., Status: completed)
...
```

## Step 5: Test Dashboard

Verify dashboard displays invoices:

```bash
# Start dashboard (in separate terminal)
streamlit run interface/dashboard/app.py

# Open browser to http://localhost:${UI_PORT:-8501}
# Check "Invoice List" tab shows invoices
```

## Step 6: Debug Common Issues

### Issue: Schema Mismatch Error

**Symptom**: `AttributeError: 'Invoice' object has no attribute 'file_path'`

**Solution**:
```bash
# Run migrations
alembic upgrade head

# Verify schema
psql $DATABASE_URL -c "\d invoices" | grep -E "storage_path|file_path"
```

### Issue: Dashboard Shows No Invoices

**Symptom**: Dashboard loads but invoice list is empty

**Debug Steps**:
1. Check database has invoices: `SELECT COUNT(*) FROM invoices;`
2. Check dashboard logs for errors
3. Verify database connection in dashboard: Check `.env` file
4. Test query directly: `python -c "from interface.dashboard.queries import get_invoice_list; import asyncio; print(asyncio.run(get_invoice_list()))"`

### Issue: API Returns 500 Error

**Symptom**: POST `/api/v1/invoices/process` returns 500

**Debug Steps**:
1. Check API logs for error traceback
2. Verify file exists: `ls -la data/grok/1.jpg`
3. Check file permissions
4. Verify database connection
5. Check for missing dependencies (OCR, PDF libraries)

### Issue: Processing Script Fails

**Symptom**: Script shows "❌ Failed" for all files

**Debug Steps**:
1. Check API is running: `curl http://localhost:${API_PORT}/health`
2. Verify file paths are correct
3. Check API logs for errors
4. Test single file manually with curl

## Step 7: Clean Up Probe Files

Move or remove temporary debugging files:

```bash
# List probe files
ls -la *.py | grep -E "probe|debug"

# Move to scripts/ (if needed for reference)
mv probe_paddle.py scripts/
mv probe_paddle_ocr.py scripts/
mv debug_invoice.py scripts/

# Or remove if no longer needed
# rm probe_paddle.py probe_paddle_ocr.py debug_invoice.py
```

## Verification Checklist

- [ ] Database schema matches code models (alembic upgrade head successful)
- [ ] API endpoint responds correctly (POST /api/v1/invoices/process works)
- [ ] Processing script works (scripts/process_invoices.py processes files)
- [ ] Dashboard displays invoices (localhost:${UI_PORT:-8501} shows invoice list)
- [ ] Error messages are clear and actionable
- [ ] Probe files cleaned up from root directory

## Next Steps

After verification, proceed with implementation:
1. Add comprehensive error logging
2. Improve dashboard error handling
3. Add database health checks
4. Test all error paths
5. Document debugging procedures

