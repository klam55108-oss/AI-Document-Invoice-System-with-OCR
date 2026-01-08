# AI E-Invoicing: Complexity Collapse E-Invoicing

An **AI-native financial automation platform** dedicated to processing heterogeneous invoice formats (PDF, Excel, Images) into structured, accurate data. We utilize an innovative **Agentic AI** approach to achieve **"Zero-Template" extraction**, overcoming the "Format Chaos" and high costs associated with legacy OCR and cloud APIs.

The project's foundational principle is the **"Complexity Collapse"** technical strategy, leveraging a cost-effective, unified, open-source stack to minimize DevOps overhead and drastically undercut expensive incumbents.

## ✨ Core Value Proposition (The Agentic Difference)

Our platform acts as an **autonomous finance agent** that doesn't just extract text, but understands and reasons over financial documents.

*   **Zero-Template Extraction:** Unlike traditional OCR which breaks when vendor layouts change, our Agentic AI uses human-level reasoning to "read, reason, and reconcile" any document.
*   **Self-Correcting Intelligence:** The platform implements a "Validation Agent" that checks internal logic. For instance, if the mathematical validation fails (Subtotal + Tax does not equal the Total), the Agentic AI automatically retries extraction using a different strategy before flagging it for human review.
*   **Universal Ingestion Funnel:** Accepts all messy formats—Excel, PDF, Images, and Emails. Files are intelligently routed: Excels go to specialized Pandas agents while complex PDFs are handled by Docling/Vision models.
*   **Conversational Intelligence:** Integration with tools like Vanna.ai allows non-technical finance managers to query data naturally, such as *"Show me the top 5 vendors by spend last month"*.

## 🏗️ Architecture: The Complexity Collapse Model

Our technical strategy is focused on maximizing intelligence while minimizing cloud expenditure (the "snowflake tax").

The infrastructure relies on the **"All-in-Postgres"** model:

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Relational Data, Vectors, Queues** | PostgreSQL (`pgvector`, `pgqueuer`) | Eliminates the need for separate Redis, Pinecone, or Snowflake instances, reducing MVP infrastructure costs significantly. |
| **Document Storage** | MinIO (S3 compatible) | Self-hosted object storage solution for storing documents.
| **Core AI Logic** | LlamaIndex / LangGraph / Pydantic | Frameworks used for Retrieval-Augmented Generation (RAG) and orchestrating Agentic workflows.
| **OCR Backend** | Docling / PaddleOCR | Cost-effective, open-source models to avoid high cloud API per-page fees.
| **Human Interface** | Streamlit Dashboard | Used for the "Human-in-the-Loop" review phase.

## 🧠 Processing Pipeline Workflow

The following Mermaid diagram illustrates the flow of an invoice from ingestion through our Agentic validation layer:

```mermaid
flowchart TD
    A[Input: PDF, Excel, Image] --> B{Universal Ingestion Funnel}
    B -- Excel --> C1[Pandas Agent Parsing]
    B -- PDF/Image --> C2[PaddleOCR / Docling]
    C1 --> D[Structured Extraction Layer]
    C2 --> D
    D --> E[LLM Extraction DeepSeek/GPT]
    E --> F{Validation Agent Math/Logic Check}
    F -- Valid --> G[STP Success: Store in Postgres]
    F -- Invalid --> H[Self-Correction Layer Prompt Refinement]
    H --> E
    F -- Still Invalid --> I[Human-in-the-Loop Review Streamlit]
    G --> J[ERP/BI Integration]
    I --> J
    I -- User Correction --> K[Feedback Loop Extraction Improves]
    K --> E
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12.2
- Docker and Docker Compose
- PostgreSQL (via Docker Compose)

### Installation

1. **Clone the repository and install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```bash
   DATABASE_URL=postgresql+asyncpg://einvoice:einvoice_dev@localhost:5432/einvoicing
   ENCRYPTION_KEY=your-generated-encryption-key-here
   LOG_LEVEL=INFO
   ```

   Generate encryption key:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Start PostgreSQL:**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the services:**
   ```bash
   # FastAPI API (port 8000)
   uvicorn interface.api.main:app --reload

   # Streamlit Dashboard (port 8501)
   streamlit run interface/dashboard/app.py
   ```

## 📊 Dashboard Features

The Streamlit dashboard (`http://localhost:8501`) provides comprehensive invoice review and analytics capabilities:

### Invoice List Tab
- **Analytics Dashboard**: Interactive charts showing:
  - Status distribution (pie chart)
  - Processing trends over time (line chart)
  - Vendor analysis (bar chart)
  - Financial summary (total amounts, tax breakdown, currency distribution)
- **Advanced Filtering**:
  - Processing status, vendor name, date range
  - Amount range (min/max)
  - Extraction confidence threshold
  - Validation status (all passed, has failed, has warning)
- **Bulk Actions**:
  - Select multiple invoices
  - Bulk reprocess with progress tracking
  - Force reprocess option
- **Export**: Download filtered invoice list as CSV

### Invoice Detail Tab
- **File Preview**: Automatic path resolution for files in `data/` or `data/encrypted/`
- **Enhanced Validation Display**:
  - Color-coded validation results with severity indicators
  - Suggested actions for failed validations
  - Grouped by status (failed, warnings, passed)
- **Missing Data Handling**: Clear indicators and explanations for missing financial fields
- **Export**: Download invoice detail as PDF report

### Key Features
- **Real-time Analytics**: Live charts updated from database
- **Smart File Resolution**: Automatically finds files in original or encrypted storage
- **User-Friendly Error Messages**: Context-aware validation errors with actionable suggestions
- **Performance Optimized**: Database indexes for fast filtering and queries

### Processing Invoices

Once your services are running, you can process invoices in several ways:

Use the provided script to process all invoices:

```bash
python scripts/process_invoices.py
```

This will process all files in the `data/` directory and show progress for each file.

#### Option 2: Process Individual Invoices via API

Process a single invoice using the API:

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/process" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "invoice-1.png",
    "category": "Invoice",
    "group": "manual",
    "force_reprocess": false
  }'
```

#### Option 3: Use the Interactive API Docs

1. Open http://localhost:8000/docs in your browser
2. Find the `POST /api/v1/invoices/process` endpoint
3. Click "Try it out" and enter the file path and optional metadata (category, group, job_id)
4. Click "Execute"

### Viewing Results

**Dashboard (Recommended):**
- Open http://localhost:8501 in your browser
- **Invoice List Tab**: View all processed invoices with status, vendor, amounts, and metadata
- **Invoice Detail Tab**: Detailed view with extracted data and validation results

**API Endpoints:**
- List invoices: `GET http://localhost:8000/api/v1/invoices`
- Get invoice details: `GET http://localhost:8000/api/v1/invoices/{invoice_id}`
- Filter by status: `GET http://localhost:8000/api/v1/invoices?status=completed`

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Understanding Processing

Each invoice goes through these stages:
1. **File Ingestion**: File is read and hashed (SHA-256) for duplicate detection
2. **OCR/Text Extraction**: Image/PDF is processed to extract text (PaddleOCR for images, Docling for PDFs)
3. **AI Extraction**: Structured data is extracted using DeepSeek-chat with manual JSON parsing for reliability (vendor, amounts, dates, etc.)
4. **Validation**: Business rules are checked (math validation, tax rate constraints, etc.)
5. **Self-Correction**: If validation fails, the system attempts to refine extraction by capping confidence and adjusting math logic
6. **Storage**: Results are stored in PostgreSQL with JSON-safe serialization

**Processing Status:**
- `pending` - Initial state
- `queued` - Added to processing queue
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed (check error_message)

### Troubleshooting

**If processing fails:**
- Check backend logs for error messages (logs include processing stage information)
- Verify the file exists in `data/` directory
- Check database connection in `.env` file: `DATABASE_URL` must be set
- Ensure all dependencies are installed: `pip install -e ".[dev]"`
- Run database migrations: `alembic upgrade head`
- Check file permissions: ensure `data/` directory is writable
- Verify file is not corrupted: check file size > 0
- Check for missing processing libraries (OCR, PDF): error messages will indicate which library is missing

**If dashboard shows no invoices:**
- Make sure you've processed at least one invoice
- Check the status filter in the sidebar (may be filtering out your invoices)
- Verify database connection: check `.env` file has `DATABASE_URL`
- Check dashboard logs for database query errors
- Verify database schema is up to date: `alembic current` should show latest migration

**API not responding:**
- Check if backend is running: `curl http://localhost:8000/health`
- Verify port 8000 is not in use by another service
- Check API logs for startup errors
- Verify database is accessible: health endpoint will show "degraded" if database issues exist

**Schema mismatch errors:**
- Run migrations: `alembic upgrade head`
- Verify migration status: `alembic current`
- Check that `storage_path` column exists in `invoices` table (not `file_path`)

**Error messages:**
- All error messages now include processing stage information
- Check logs for detailed error context including file path, invoice ID, and stage
- Error messages are user-friendly and indicate what failed and where

**PaddleOCR warnings and resource usage:**
- First-time image processing will show verbose PaddleOCR model loading messages
- These are harmless informational messages - models are being cached
- Subsequent requests will be faster and quieter
- To suppress warnings in curl, redirect stderr: `curl ... 2>/dev/null`
- The warnings are automatically suppressed in the application logs
- **IMPORTANT**: OCR initialization is now non-blocking and runs in a thread pool
- This prevents system crashes and resource exhaustion
- First request may take 30-60 seconds for model loading
- Use `--max-time 120` with curl to set a timeout
- File size limit: 100MB maximum per file

### Current Implementation Status

**✅ Completed (Scaffold Phase):**
- Project structure with three-layer architecture (Sensory, Brain, Interaction)
- PostgreSQL database with pgvector extension
- Async SQLAlchemy 2.0 ORM models
- File processing pipeline (PDF, Excel, CSV, Images)
- Basic data extraction and validation framework
- FastAPI REST API with async endpoints
- Streamlit review dashboard
- File-level encryption at rest
- SHA-256 file hashing for duplicate detection
- Database migrations with Alembic

**✅ Recently Completed (Ingestion Workflow Fixes):**
- Non-blocking PaddleOCR initialization (prevents system crashes)
- Comprehensive error handling with user-friendly messages
- Database schema health checks and connection retry logic
- Enhanced logging with processing stage tracking
- OCR timeout handling with retry logic (180s default, up to 10min for large images)
- File validation (size limits, corruption checks)
- Background processing with proper session management
- Status tracking with immediate database commits
- Performance monitoring (processing time tracking)

**✅ Completed (Agentic Phase):**
- Docling integration for advanced PDF processing
- DeepSeek-chat integration as primary extraction LLM
- pgqueuer setup for background job management
- Enhanced validation rules (Tax rate auto-detection, Line item math fallback)
- Chatbot engine for conversational invoice querying
- Robust transaction management with explicit rollbacks

**🚧 Future Roadmap:**
- Multi-agent coordination for complex multi-page document reconciliation
- Integration with external ERP (Odoo/SAP) APIs
- Enhanced local embedding model performance tuning

## 📚 Documentation

- **[Setup & Scaffold](./docs/setup-scaffold-1.md)**: Complete implementation documentation
- **[Invoice Processing](./docs/process-images-3.md)**: Recent improvements and enhancements
- **[Duplicate Processing Logic](./docs/duplicate-processing-logic.md)**: How file versioning and duplicate detection works
- **[Multi-Agent Architecture](./docs/multi-agents-2.md)**: Agentic AI implementation details
