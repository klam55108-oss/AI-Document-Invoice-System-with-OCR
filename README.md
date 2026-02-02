# AI E-Invoicing: Complexity Collapse

An **AI-native financial automation platform** for processing heterogeneous invoice formats (PDF, Excel, Images) into structured data. Leveraging **Agentic AI** for "Zero-Template" extraction and self-correcting validation.

---

## 📸 Implementation at a Glance

| Overview | Invoice List & Bulk Actions |
|----------|-----------------------------|
| ![E-Invoice Review Dashboard – overview, filters, and status distribution](assets/1.png) | ![Invoice list table, export, and bulk reprocess](assets/2.png) |

| Invoice Detail & Extracted Data | Validation Analysis |
|----------------------------------|---------------------|
| ![Single invoice view with file preview and extracted fields](assets/3.png) | ![Validation rules: passed, failed, and warnings](assets/4.png) |

| Upload Files | Chat with Invoices |
|--------------|--------------------|
| ![Drag-and-drop upload for PDF, Excel, and images](assets/5.png) | ![Natural-language chatbot over invoice data](assets/6.png) |

| Quality Metrics | Financial Summary |
|-----------------|-------------------|
| ![Extraction quality, confidence, and format distribution](assets/7.png) | ![Total amount, tax breakdown, and currency distribution](assets/8.png) |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12.2+
- Docker and Docker Compose
- PostgreSQL (Automated via Docker)

### 2. Setup
```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
# Create .env with:
# DATABASE_URL=postgresql+asyncpg://einvoice:einvoice_dev@localhost:${PGDB_PORT:-5432}/einvoicing
# ENCRYPTION_KEY=your-key (Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
# API_PORT=8000, UI_PORT=8501
```

### 3. Start Services
```bash
# Start Database
docker-compose up -d

# Run Migrations
alembic upgrade head

# Start API
python interface/api/main.py --reload

# Start Dashboard (Port 8501)
streamlit run interface/dashboard/app.py
```

---

## 📄 Usage

### Process Invoices
Run the consolidated script to process files in the `data/` directory:
```bash
$ python scripts/process_invoices.py
$ python scripts/process_invoices.py --recursive --dir data/ --force --concurrency 2
$ python scripts/process_invoices.py --dir data/jimeng --pattern "invoice-1.png" --force --background --api-url "http://127.0.0.1:8800"
```

Or via API:
```bash
curl -X POST "http://localhost:8000/api/v1/invoices/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "invoice-1.png"}'
```

### View Results
- **Dashboard**: [http://localhost:8501](http://localhost:8501)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🏗️ Technical Overview

| Layer | Technology |
| :--- | :--- |
| **Persistence** | PostgreSQL (`pgvector`, `pgqueuer`) |
| **Logic** | LlamaIndex, DeepSeek, Docling |
| **Interface** | FastAPI, Streamlit |

---

## 📚 Documentation
- **[Technical Stack & Architecture](./docs/tech-stack.md)** — Stack by layer, alternatives, and processing logic.
- **[Setup & Scaffold](./docs/setup-scaffold-1.md)** — Step-by-step implementation guide.
- **[Dashboard Improvements](./docs/002-dashboard-improvements.md)** — Analytics, export, filters, and bulk actions.
- **[Dataset Upload UI](./docs/003-dataset-upload-ui-implementation.md)** — Web upload and processing flow.
- **[Invoice Chatbot](./docs/004-invoice-chatbot-implementation.md)** — RAG-backed chat over invoice data.
- **[Duplicate Processing Logic](./docs/duplicate-processing-logic.md)** — Hashing and versioning.
- **[Resilient Configuration](./docs/resilient-configuration.md)** — Module plugability and runtime configuration APIs.
- **[Docs Index](./docs/README.md)** — Full documentation index and RAG stack analysis.
