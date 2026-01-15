# AI E-Invoicing: Complexity Collapse

An **AI-native financial automation platform** for processing heterogeneous invoice formats (PDF, Excel, Images) into structured data. Leveraging **Agentic AI** for "Zero-Template" extraction and self-correcting validation.

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
- **[Technical Stack & Architecture](./docs/tech-stack.md)**: Detailed breakdown, alternatives, and processing logic.
- **[Setup & Scaffold](./docs/setup-scaffold-1.md)**: Step-by-step implementation guide.
- **[Duplicate Processing Logic](./docs/duplicate-processing-logic.md)**: How hashing and versioning works.
- **[Multi-Agent Architecture](./docs/multi-agents-2.md)**: Advanced RAG and agent patterns.
- **[Resilient Configuration](./docs/resilient-configuration.md)**: Module plugability, runtime configuration APIs, and workflow diagram.
