# 🚀 Quick Start Guide

Your AI E-Invoicing application is now running with:
- **Backend API**: http://localhost:8000
- **Frontend Dashboard**: http://localhost:8501
- **20 Invoice Images**: Ready in `data/` folder

## 📋 How to Process Your Invoices

### Option 1: Process All Invoices at Once (Recommended)

Use the provided script to process all 20 invoices:

```bash
python scripts/process_all_invoices.py
```

This will:
- Process all `invoice-*.png` files in the `data/` directory
- Show progress for each file
- Display a summary at the end

### Option 2: Process Individual Invoices via API

You can process invoices one at a time using the API:

```bash
# Process a single invoice
curl -X POST "http://localhost:8000/api/v1/invoices/process" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "invoice-1.png",
    "force_reprocess": false
  }'
```

Or using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/invoices/process",
    json={
        "file_path": "invoice-1.png",
        "force_reprocess": False
    }
)
print(response.json())
```

### Option 3: Use the Interactive API Docs

1. Open http://localhost:8000/docs in your browser
2. Find the `POST /api/v1/invoices/process` endpoint
3. Click "Try it out"
4. Enter the file path (e.g., `invoice-1.png`)
5. Click "Execute"

## 📊 View Results

### Dashboard (Recommended)

1. Open http://localhost:8501 in your browser
2. You'll see:
   - **Invoice List Tab**: All processed invoices with status
   - **Invoice Detail Tab**: Detailed view of a specific invoice

### API Endpoints

**List all invoices:**
```bash
curl "http://localhost:8000/api/v1/invoices?page=1&page_size=20"
```

**Get specific invoice details:**
```bash
# Replace {invoice_id} with actual UUID from the list
curl "http://localhost:8000/api/v1/invoices/{invoice_id}"
```

**Filter by status:**
```bash
# Get only completed invoices
curl "http://localhost:8000/api/v1/invoices?status=completed"
```

## 🔍 Understanding Processing Status

Each invoice goes through these statuses:
- `pending` - Initial state
- `queued` - Added to processing queue
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed (check error_message)

## 📝 What Happens During Processing

1. **File Ingestion**: File is read and hashed (SHA-256)
2. **OCR/Text Extraction**: Image is processed to extract text
3. **AI Extraction**: Structured data is extracted (vendor, amounts, dates, etc.)
4. **Validation**: Business rules are checked (math, dates, etc.)
5. **Self-Correction**: If validation fails, AI attempts to refine extraction
6. **Storage**: Results are stored in PostgreSQL

## 🛠️ Troubleshooting

**If processing fails:**
- Check backend logs for error messages
- Verify the file exists in `data/` directory
- Check database connection in `.env` file
- Ensure all dependencies are installed

**If dashboard shows no invoices:**
- Make sure you've processed at least one invoice
- Check the status filter in the sidebar
- Verify database connection

**API not responding:**
- Check if backend is running: `curl http://localhost:8000/health`
- Verify port 8000 is not in use by another service

## 🎯 Next Steps

After processing invoices:
1. Review extracted data in the dashboard
2. Check validation results for any issues
3. Use the API to query specific invoices
4. Integrate with your ERP/accounting system

## 📚 API Documentation

Full API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

