# OCR Switch Options Summary

## Overview

This update introduces switchable OCR providers (PaddleOCR and DeepSeek OCR) with side-by-side comparison, CPU-only DeepSeek OCR support, and admin-controlled provider configuration.

## Highlights

- Added OCR provider configuration (default + enabled list) via environment settings.
- Added OCR API endpoints for provider listing, run, compare, and result retrieval.
- Added OCR comparison response to include both providers' results and key fields.
- Added DeepSeek OCR integration (OpenAI-compatible, CPU-only).
- Added persistence for OCR results and comparisons (models + Alembic migration).
- Added tests for OCR run/compare/provider configuration.
- Added a Streamlit dashboard tab for OCR comparison.

## Key Files

- `core/ocr/` (configuration, providers, service, repository)
- `ingestion/image_processor.py` (provider-aware OCR)
- `ingestion/pdf_processor.py` (provider-aware OCR fallback)
- `interface/api/routes/ocr.py` + `interface/api/schemas.py`
- `alembic/versions/c2f1b8e0b1a1_add_ocr_records.py`
- `interface/dashboard/components/ocr_compare.py`
- `interface/dashboard/app.py`
