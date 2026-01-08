# CSV and XLSX Processing Implementation

This document describes the technical implementation and workflow for processing tabular invoice data (CSV, XLSX, XLS) within the AI e-Invoicing system.

## Overview

The system treats tabular files as highly-structured text inputs. Unlike PDF/Image processing which requires OCR, tabular processing leverages the native structure of the files using `pandas` to ensure 100% text accuracy before passing the data to the LLM-based extraction layer.

## Technology Stack

| Layer | Component | Technology |
| :--- | :--- | :--- |
| **Ingestion** | `excel_processor.py` | `pandas`, `openpyxl`, `tabulate` |
| **Orchestration** | `orchestrator.py` | `asyncio`, `pathlib` |
| **Brain** | `extractor.py` | `DeepSeek-V3` / `GPT-4o`, `Direct OpenAI Client` |
| **Core** | `models.py` | `SQLAlchemy 2.0`, `PostgreSQL (JSONB)` |
| **Interface** | `invoices.py` | `FastAPI`, `Pydantic v2` |

## Workflow

### 1. File Discovery & Type Detection
- **Trigger**: User uploads a file or a batch processing script (e.g., `process_invoices.py`) is run.
- **Detection**: `ingestion.file_discovery.get_file_type` identifies `.csv`, `.xlsx`, or `.xls` extensions.
- **Routing**: `ingestion.orchestrator.process_invoice_file` dispatches the file to the `process_excel` handler.

### 2. Tabular Ingestion (`ingestion/excel_processor.py`)
- **Reading**: `pandas.read_csv` or `pandas.read_excel` loads the data into DataFrames.
- **Multi-Sheet Support**: For Excel files, every sheet is parsed and converted.
- **Textualization**: The DataFrames are converted to a **Markdown representation** using `df.to_markdown()`. This preserves the column-row relationships in a way that LLMs can easily parse.
- **Return**: A dictionary containing the combined markdown text, sheet-wise record counts, and metadata.

### 3. Smart Extraction (`brain/extractor.py`)
- **Contextual Prompting**: The system prompt includes specific instructions for "TABULAR DATA":
    > "Pay close attention to data columns. The raw text might look like a table or delimited text. Map the columns correctly to the schema."
- **LLM Processing**: The LLM analyzes the markdown table and maps it to the `ExtractedDataSchema` (Vendor, Date, Line Items, etc.).
- **Self-Correction**: If the first extraction fails validation (e.g., math mismatch), the `refine_extraction` logic provides the tabular text back to the LLM with error feedback for a second attempt.

### 4. Storage & Storage (`core/models.py`)
- **Invoice Record**: Metadata (filename, hash, size) is stored in the `invoices` table.
- **Structured Data**: The extracted fields and line items are stored in the `extracted_data` table, with line items persisting in a `JSONB` column.
- **Raw Traceability**: The full markdown representation generated during ingestion is saved in the `raw_text` field for debugging and human review.

## Folder Structure Summary

- `ingestion/`: Contains `excel_processor.py` (the core parser).
- `brain/`: Handles the mapping of tabular text to structured fields.
- `core/`: Defines the database schema and data models.
- `interface/`: Provides the API endpoints to trigger processing.
- `data/`: The directory where input files are stored/scanned.

## Performance Considerations
- **Parallelism**: Since CSV/XLSX processing is memory-efficient (unlike heavy OCR), many files can be processed in parallel via the `pgqueuer` background system.
- **Memory**: Large Excel files are handled via `pandas` streaming/parsing, though typically invoice files are small.
