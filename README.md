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
    B -- PDF/Image --> C2[Docling / PaddleOCR]
    C1 --> D[Structured Extraction Layer]
    C2 --> D
    D --> E[LlamaIndex Extraction & RAG]
    E --> F{Validation Agent<br>Math/Logic Check}
    F -- Valid --> G[STP Success:<br>Store in Postgres]
    F -- Invalid --> H[Agent Retries or<br>Vendor Lookup &#91;RAG&#93;]
    H --> E
    F -- Still Invalid --> I[Human-in-the-Loop<br>Review &#91;Streamlit&#93;]
    G --> J[ERP/BI Integration]
    I --> J
    I -- User Correction --> K[Retrain/Update Agent<br>Extraction Improves]
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

### Processing Invoices

Once your services are running, you can process invoices in several ways:

#### Option 1: Process All Invoices at Once (Recommended)

Use the provided script to process all invoices:

```bash
python scripts/process_all_invoices.py
```

This will process all `invoice-*.png` files in the `data/` directory and show progress for each file.

#### Option 2: Process Individual Invoices via API

Process a single invoice using the API:

```bash
curl -X POST "http://localhost:8000/api/v1/invoices/process" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "invoice-1.png",
    "force_reprocess": false
  }'
```

#### Option 3: Use the Interactive API Docs

1. Open http://localhost:8000/docs in your browser
2. Find the `POST /api/v1/invoices/process` endpoint
3. Click "Try it out" and enter the file path
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
2. **OCR/Text Extraction**: Image/PDF is processed to extract text (PaddleOCR for images)
3. **AI Extraction**: Structured data is extracted using LlamaIndex RAG (vendor, amounts, dates, etc.)
4. **Validation**: Business rules are checked (math validation, date consistency, etc.)
5. **Self-Correction**: If validation fails, AI attempts to refine extraction
6. **Storage**: Results are stored in PostgreSQL

**Processing Status:**
- `pending` - Initial state
- `queued` - Added to processing queue
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed (check error_message)

### Troubleshooting

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

**🚧 In Progress / Planned:**
- Docling integration for advanced PDF processing
- OCR integration (DeepSeek-OCR/PaddleOCR) for image processing
- LlamaIndex RAG integration for agentic extraction
- pgqueuer extension setup for job queue management
- Enhanced validation rules and self-correcting intelligence

## 📚 Documentation

- **[Setup & Scaffold](./docs/setup-scaffold-1.md)**: Complete implementation documentation
- **[Invoice Processing](./docs/process-images-3.md)**: Recent improvements and enhancements
- **[Duplicate Processing Logic](./docs/duplicate-processing-logic.md)**: How file versioning and duplicate detection works
- **[Multi-Agent Architecture](./docs/multi-agents-2.md)**: Agentic AI implementation details
