Based on the sources and our technical strategy, here is the clarification and bootstrap plan for your project.

### **1. Language: Is it all Python?**
**Yes, the entire backend, AI orchestration, and data pipeline will use Python.** The sources explicitly highlight Python-based frameworks like **LlamaIndex, LangChain, and FastAPI** for building the RAG and Agentic AI workflows. Furthermore, core data processing and OCR libraries such as **Pandas, PyTorch, and DeepSeek-OCR** are Python-native.

### **2. Simplicity for POC/MVP**
To keep the initial implementation as simple as possible, the sources recommend a **"local-first" tech stack**. Instead of deploying to the cloud immediately, you can build and test the workflow on your laptop (e.g., a MacBook). 
*   **Start small:** Use a handful of sample invoices (PDF, Image, and Excel) to validate the "Sensory" layer first.
*   **API-First:** You can initially skip a complex frontend and focus on a **FastAPI** backend to expose endpoints for querying your invoices.

### **3. Configuration and Virtual Environments**
*   **`pyproject.toml` (not .xml):** In modern Python development, `pyproject.toml` is the standard for managing project metadata and dependencies. (Note: The mention of `.toml` over `.xml` is a standard Python practice and not explicitly in the sources). 
*   **Virtual Environments:** For a simple POC/MVP, it is **recommended to use a single virtual environment** for the entire project. This keeps dependency management straightforward. As the project scales into a SaaS with separate Dockerized containers for OCR and API services, you can move toward individual environments for each module.

### **4. Refined Bootstrap Details**

You can copy and use this summary to initialize your project:

**Project Name:** `AgenticAP` (Complexity Collapse E-Invoicing)
**Strategy:** **"Complexity Collapse"** — using PostgreSQL for everything (data, vectors, and queues) to minimize costs.

#### **Project Folder Structure**
```text
AgenticAP/
├── core/           # Infrastructure: Postgres connection, pgvector, pgqueuer
├── ingestion/      # Sensory Layer: DeepSeek-OCR, Docling, Pandas parsing
├── brain/          # Brain Layer: LlamaIndex, Pydantic schemas, RAG logic
├── interface/      # Interaction Layer: FastAPI endpoints, Streamlit UI
├── data/           # Local storage for sample invoices (PDF, CSV, XLSX)
└── pyproject.toml  # Unified dependency management
```

#### **Core Tech Stack for the MVP**
*   **Language:** Python 3.10+.
*   **Database:** **PostgreSQL** with `pgvector` (Vectors) and `pgqueuer` (Jobs).
*   **OCR Engine:** **DeepSeek-OCR** (for structured JSON output) or **Docling**.
*   **AI Framework:** **LlamaIndex** or **LangGraph** for Agentic reasoning.
*   **File Storage:** **MinIO** (S3 compatible) or local disk for the POC.
*   **API/UI:** **FastAPI** (for the engine) and **Streamlit** (for the review dashboard).

#### **Immediate Implementation Steps**
1.  **Environment Setup:** Create a virtual environment and install `fastapi`, `llama-index`, `pydantic`, `sqlalchemy`, and `deepseek-ocr`.
2.  **Sensory Layer (Week 1-4):** Write a script to take an invoice from the `data/` folder, run it through **DeepSeek-OCR**, and save the resulting JSON/Text to **Postgres**.
3.  **Brain Layer (Week 5-8):** Define a **Pydantic schema** for an invoice (Vendor, Date, Total, Tax). Implement a "Validation Agent" that checks if `Subtotal + Tax == Total`.
4.  **Interaction Layer (Week 9-12):** Build a **Streamlit** page that displays the extracted data and highlights any mathematical errors found by the agent for human review.

***

**Analogy for Understanding:**
Think of this bootstrap plan like **building a smart house**. The **`core/`** is the foundation and wiring (Postgres); the **`ingestion/`** is the front door sensors (OCR) that identify who is coming in; the **`brain/`** is the smart-home hub that decides if the visitor is allowed (Validation Agent); and the **`interface/`** is the tablet on your wall where you control everything. Using one virtual environment for the MVP is like using one master key for all the doors while you're still under construction.