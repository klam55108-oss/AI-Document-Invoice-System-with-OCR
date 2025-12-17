# AgenticAP: Complexity Collapse E-Invoicing

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

## 🚀 Codes

Coming soon.
