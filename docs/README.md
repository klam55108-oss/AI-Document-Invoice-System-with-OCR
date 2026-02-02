# Documentation Index

Reference for the current AI E-Invoicing implementation: dashboard, API, ingestion, and configuration.

## Implementation summaries

| Doc | Description |
|-----|-------------|
| [Technical Stack & Architecture](./tech-stack.md) | Stack by layer (frontend, API, processing, intelligence, data), alternatives, and processing logic |
| [Setup & Scaffold](./setup-scaffold-1.md) | Step-by-step setup and scaffold guide |
| [Dashboard Improvements](./002-dashboard-improvements.md) | Analytics, export to CSV/PDF, filters, bulk reprocess, status/vendor/financial charts |
| [Dataset Upload UI](./003-dataset-upload-ui-implementation.md) | Web upload (PDF, Excel, images), processing flow, and upload API |
| [Invoice Chatbot](./004-invoice-chatbot-implementation.md) | RAG chatbot: sessions, rate limiting, vector retriever, DeepSeek, dashboard tab |
| [Ingestion Workflow Fixes](./005-ingestion-workflow-fixes.md) | Ingestion pipeline fixes and behavior |
| [Duplicate Processing Logic](./duplicate-processing-logic.md) | File hashing, versioning, and duplicate handling |
| [Resilient Configuration](./resilient-configuration.md) | Module plugability, runtime configuration APIs, workflow diagram |
| [OCR Implementation](./ocr-implementation.md) | OCR providers, configuration, and compare flow |
| [OCR Switch Options](./ocr-switch-options.md) | Switching and configuring OCR providers |
| [CSV Implementation](./csv-implementation.md) | CSV ingestion and processing |
| [PDF Implementation](./pdf-implementation.md) | PDF processing (Docling/PyPDF) |
| [Process Images](./process-images-3.md) | Image processing and pipeline |

## API surface (current)

- **Health**: `GET /api/v1/health`
- **Invoices**: process, list, detail, analytics (status-distribution, time-series, vendor-analysis, financial-summary)
- **Uploads**: upload files, list, status
- **Chatbot**: `POST /api/v1/chatbot/chat`, session management
- **Quality**: extraction quality and confidence metrics
- **Configurations**: module/stage configuration, activation, rollback
- **OCR**: providers, compare, run
- **Modules / Stages**: configuration metadata

## Dashboard tabs (Streamlit)

Invoice List (filters, bulk actions, export) → Invoice Detail (preview, extracted data, validation analysis) → Upload Files → Chatbot → Quality Metrics → OCR Compare.

---

# Analysis of AI-EInvoicing RAG & Autonomy Stack

## 1. Executive Summary

**Is the implementation reasonable?**
**Yes, highly reasonable.** The current architecture leverages a "Complexity Collapse" strategy by using powerful inference-only models (DeepSeek-V3/GPT-4o) combined with **LlamaIndex** for RAG and **pgvector** for storage.

Your confusion likely stems from the fact that **SFT (Supervised Fine-Tuning)** and **TRL (Transformer Reinforcement Learning)** are **NOT** currently used in this project, nor are they typically required for this stage of an invoice extraction application.

## 2. Technology Breakdown & Clarification

### ✅ Currently Implemented

| Technology | Role | Status | Why it's a good choice |
|------------|------|--------|------------------------|
| **LlamaIndex** | RAG Framework | **Core** | specialized for "Data Context" and structured extraction, making it often superior to LangChain for document-heavy tasks like invoicing. |
| **pgvector** | Vector Store | **Core** | Integrated directly into PostgreSQL, reducing infrastructure complexity (no need for Pinecone/Qdrant). |
| **DeepSeek-V3** | Inference Model | **Core** | Extremely cost-effective ($0.14/1M tokens) with performance comparable to top-tier models for extraction. |
| **Docling** | PDF Parser | **Core** | Preserves layout structure, which is critical for accurate RAG on invoices. |

### ❌ Not Implemented (and likely not needed yet)

| Technology | Role | Status | Recommendation |
|------------|------|--------|----------------|
| **SFT (Supervised Fine-Tuning)** | Training | **Absent** | **Not recommended yet.** Fine-tuning is complex and expensive. Modern LLMs (like DeepSeek) are usually capable enough with just good prompting (RAG). Only consider SFT if you have 10,000+ examples and general models fail. |
| **TRL (Transformer Reinforcement Learning)** | RLHF Training | **Absent** | **Overkill.** This is for training models to follow instructions (like ChatGPT itself). You do not need this for an invoice extractor. |
| **LangChain** | Orchestration | **Absent** | **Redundant.** You are using LlamaIndex, which overlaps significantly with LangChain. Using both introduces unnecessary complexity ("dependency hell"). |

## 3. Detailed Component Analysis

### A. RAG Implementation (LlamaIndex + pgvector)

The implementation focuses on **Context-Aware Extraction**:

1. **Ingest**: PDFs are parsed (Docling) and Chunked.
2. **Retrieve**: Relevant chunks are found using vector similarity (pgvector).
3. **Generate**: The LLM extracts specific fields (Vendor, Total, Date) based on that context.
4. **Validate**: Pydantic models ensure the output matches the required format.

**Verdict**: This is the industry-standard approach for modern Document AI. It is robust and easier to maintain than training custom models.

### B. "Agentic" Autonomy

The project uses **LlamaIndex Agents** (ReAct pattern) which can:

* Reason about what information is missing.
* Query the vector store specifically for that missing info.
* Self-correct if validation fails (e.g., if Total != Subtotal + Tax).

**Verdict**: This is a practical implementation of "Agency" without over-engineering.

## 4. Suggestions for Improvement

While the stack is solid, here are 3 targeted improvements:

### 1. Hybrid Search (Keyword + Vector)

**Current**: Relies heavily on Vector Search (`pgvector`).
**Problem**: Vector search sometimes misses exact keyword matches (e.g., specific Invoice ID "INV-9928").
**Suggestion**: Implement **Hybrid Search**.

* Use `pgvector` for semantic meaning ("find huge software bills").
* Use PostgreSQL `tsvector` (Full Text Search) for exact keywords ("INV-9928").
* Combine results using Reciprocal Rank Fusion (RRF).
* *Note: You have a skill available for this: `pgvector-search`.*

### 2. Evaluation Pipeline (The Missing Piece)

**Current**: Reliance on "vibes" or manual checking.
**Problem**: You don't know if a prompt change improved extraction by 1% or broke it by 5%.
**Suggestion**: Implement a **RAG Evaluation (Ragas / TruLens)**.

* Create a "Golden Dataset" of 50 perfectly extracted invoices.
* Run your pipeline against them.
* Metrics: *Answer Relevancy* and *Faithfulness*.

### 3. Small-Model Fine-Tuning (Future Step)

**Current**: Using large API models (DeepSeek/GPT-4o).
**Future**: If you process millions of invoices, costs will add up.
**Suggestion**: **Distillation / SFT** (Only massive scale).

* Use GPT-4o to generate training data.
* Fine-tune a small local model (Llama-3-8B) using **TRL/SFT** to do *specifically* invoice extraction.
* This would confirm where TRL/SFT fits in—it's an *optimization* step, not a starting point.

## 5. Summary

You are **not** missing out by excluding LangChain or TRL. You have chosen a **focused, high-performance stack** (LlamaIndex) that is perfectly suited for your problem domain.

**Recommendation**: Stay the course. Focus on **Hybrid Search** and **Evaluation** rather than adding training complexity.

## External references

- [omniparser (GitHub)](https://github.com/omniscale/omniparser): Universal ETL engine for tabular data (CSV, Excel, JSON, XML, etc.) with streaming parsing and rich type-system.
- [TRL (GitHub)](https://github.com/huggingface/trl): Library by Hugging Face for training and fine-tuning language models with reinforcement learning and supervised fine-tuning (SFT) techniques.
- [Supervised Fine Tuning (SFT) (Docs)](https://huggingface.co/docs/trl/main/en/sft_trainer): Train language models using supervised learning techniques for efficient fine-tuning.