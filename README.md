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

````mermaid
graph TD
    A[Input: PDF, Excel, Image] --> B{Universal Ingestion Funnel};
    B -->|Excel| C1[Pandas Agent Parsing];
    B -->|PDF/Image| C2[OCR/Vision Models Docling/PaddleOCR];
    C1 --> D[Structured Extraction Layer];
    C2 --> D;
    D --> E[LlamaIndex: Agentic Extraction & RAG];
    E --> F{Validation Agent: Check Math/Logic against Pydantic Schema};
    F -->|Valid| G[STP Success: Store Final Data in Postgres];
    F -->|Invalid/Need Context| H[Agent Retries/RAG Lookup for Vendor Context];
    H --> F;
    F -->|Still Invalid| I[Human-in-the-Loop Review Dashboard Streamlit];
    G --> J[Output: ERP Integration];
    I --> J;
````

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

For detailed implementation documentation, see [docs/implementation-scaffold.md](./docs/implementation-scaffold.md).

