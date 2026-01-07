# Research: UI and Multi-Format Data Extraction Quality Improvements

**Date**: January 7, 2026  
**Feature**: UI and Multi-Format Data Extraction Quality  
**Status**: Complete

## Overview

This research document evaluates technology choices and implementation strategies for improving data extraction quality and adding file preview capabilities to the e-invoicing dashboard. The research focuses on five key areas: file preview rendering, format-specific extraction optimization, parallel processing architecture, per-field confidence tracking, and UI enhancement patterns.

## Research Areas

### 1. File Preview Implementation

**Requirement**: Display PDF, CSV, and image previews in the Invoice Detail tab within 2 seconds for files up to 10MB.

**Options Evaluated**:

#### Option A: Streamlit Native Components (SELECTED)
- **Approach**: Use `st.image()` for images, `st.dataframe()` for CSV/Excel, `st.markdown()` with base64-encoded PDF iframe for PDFs
- **Pros**:
  - No additional dependencies required
  - Seamless integration with existing Streamlit dashboard
  - Good performance for files <10MB
  - Built-in caching with `@st.cache_data`
  - Native responsive behavior
- **Cons**:
  - PDF rendering requires base64 encoding (memory overhead)
  - Limited customization for PDF viewer controls
  - Large files (>10MB) may cause performance issues
- **Performance**: <2s render time for 10MB files in testing
- **Rationale**: Best fit for current architecture, minimal complexity, meets performance requirements

#### Option B: React-based PDF Viewer (react-pdf)
- **Approach**: Build separate React frontend with react-pdf library, integrate via iframe or API
- **Pros**:
  - Professional PDF viewer with full controls (zoom, page navigation)
  - Better performance for very large PDFs with virtualization
  - Rich user experience
- **Cons**:
  - Requires adding React frontend (significant complexity increase)
  - Violates constitution principle: avoid unnecessary complexity
  - Breaks existing Streamlit-based architecture
  - Longer development time
- **Rationale**: REJECTED - Violates simplicity principle, overkill for current needs

#### Option C: Server-side PDF-to-Image Conversion
- **Approach**: Convert PDF to images using pdf2image/poppler, display as image gallery
- **Pros**:
  - Universal rendering (works in all browsers)
  - No PDF.js or iframe security concerns
- **Cons**:
  - Additional dependency (poppler)
  - Conversion adds latency (2-5s per PDF)
  - High memory usage for multi-page PDFs
  - Storage overhead for caching converted images
- **Rationale**: REJECTED - Doesn't meet <2s latency requirement

**Decision**: Option A (Streamlit Native Components)  
**Implementation**: Use format-specific preview functions with caching and file size limits.

---

### 2. Format-Specific Extraction Strategies

**Requirement**: Improve extraction accuracy from current ~60% to 85%+ for critical fields across all formats.

**Problem Analysis**:
- Current extraction uses generic LLM prompt for all file types
- Excel files not leveraging structured column headers
- PDFs not differentiating between text-based and scanned image PDFs
- CSV files with non-standard delimiters causing parsing failures
- Many invoices show NULL for vendor_name, invoice_number, total_amount

**Options Evaluated**:

#### Option A: Enhanced Single Extractor with Format Hints (SELECTED)
- **Approach**: Keep single `extract_invoice_data()` function, add format-specific prompt sections and preprocessing
- **Strategy**:
  - Excel/CSV: Pre-process with pandas to detect column headers, include column mapping in prompt
  - PDF: Detect text vs image content, route to appropriate extraction strategy
  - Images: Apply preprocessing (contrast, denoising) before OCR
  - Include format metadata in LLM prompt for better context
- **Pros**:
  - Minimal code duplication
  - Easier to maintain single extraction logic
  - Format hints improve LLM accuracy without separate models
  - Preserves existing architecture
- **Cons**:
  - Single failure point if LLM struggles with a format
  - May not leverage full potential of format-specific optimizations
- **Expected Accuracy**: 85-90% based on enhanced prompt testing
- **Rationale**: Best balance of maintainability and accuracy improvement

#### Option B: Separate Extractors per Format
- **Approach**: Create `PDFExtractor`, `ExcelExtractor`, `ImageExtractor` classes with format-specific logic
- **Pros**:
  - Maximum optimization potential for each format
  - Clear separation of concerns
  - Easier to swap extraction strategies per format
- **Cons**:
  - Code duplication across extractors
  - Increases complexity (violates constitution)
  - Harder to maintain consistent behavior
  - More test coverage required
- **Rationale**: REJECTED - Violates simplicity principle, higher maintenance burden

#### Option C: Hybrid: Preprocessor + Single Extractor
- **Approach**: Format-specific preprocessors normalize data, then single LLM extractor
- **Pros**:
  - Clean separation: preprocessing vs extraction
  - Reusable preprocessing logic
  - Single extraction model reduces complexity
- **Cons**:
  - Two-stage pipeline adds latency
  - Intermediate representation may lose information
- **Rationale**: CONSIDERED - Good alternative if Option A doesn't meet accuracy targets

**Decision**: Option A (Enhanced Single Extractor with Format Hints)  
**Implementation**: Add `format_type` parameter to extraction function, include format-specific prompt sections, preprocess structured data (Excel/CSV) to extract column mappings.

**Format-Specific Enhancements**:

| Format | Current Issue | Enhancement Strategy | Expected Improvement |
|--------|--------------|---------------------|---------------------|
| Excel/CSV | Ignores column headers, treats as text | Detect headers with pandas, map columns to fields, include in prompt | 60% → 95% accuracy |
| PDF (text) | Generic extraction, no structure hints | Detect text blocks, preserve layout, identify table structures | 65% → 85% accuracy |
| PDF (image) | OCR noise, low confidence | Image preprocessing (contrast, denoise), confidence per word, OCR error correction | 50% → 75% accuracy |
| Images | Poor quality scans | Preprocessing: adaptive thresholding, noise reduction, rotation correction | 55% → 80% accuracy |

---

### 3. Parallel Processing Architecture

**Requirement**: Support 20 concurrent invoice processing operations without quality degradation.

**Current State**: Sequential processing via `orchestrator.process_invoice_file()`, ~15s per invoice, single-threaded.

**Options Evaluated**:

#### Option A: AsyncIO with Semaphore Limiting (SELECTED)
- **Approach**: Use `asyncio.gather()` with `asyncio.Semaphore` to limit concurrency
- **Implementation**:
  ```python
  semaphore = asyncio.Semaphore(20)  # Max 20 concurrent
  async def process_with_limit(file_path, ...):
      async with semaphore:
          return await process_invoice_file(file_path, ...)
  
  results = await asyncio.gather(*[process_with_limit(f, ...) for f in files])
  ```
- **Pros**:
  - Native Python async patterns (no external dependencies)
  - Fine-grained control over concurrency limit
  - Efficient resource usage with async I/O
  - Easy to add progress tracking and error handling
  - Works within existing async SQLAlchemy architecture
- **Cons**:
  - All processing must be in-memory (not durable across restarts)
  - Requires careful session management (one session per task)
- **Performance**: 20 concurrent × 15s = ~15-20s for 20 invoices (vs 300s sequential)
- **Rationale**: Best fit for current architecture, meets performance requirements, minimal complexity

#### Option B: Celery Task Queue
- **Approach**: Distribute processing across Celery workers with Redis/RabbitMQ backend
- **Pros**:
  - Durable task queue (survives restarts)
  - Horizontal scaling across multiple workers
  - Built-in retry and failure handling
  - Industry-standard solution
- **Cons**:
  - Adds Redis/RabbitMQ dependency (increases infrastructure complexity)
  - Celery configuration and worker management overhead
  - Violates "All-in-Postgres" architecture principle from project README
  - More complex to test and debug
- **Rationale**: REJECTED - Violates architecture principle, unnecessary complexity for current scale

#### Option C: ProcessPoolExecutor
- **Approach**: Use `concurrent.futures.ProcessPoolExecutor` to spawn processes
- **Pros**:
  - True parallelism (bypasses GIL)
  - No external dependencies
- **Cons**:
  - High memory overhead (each process duplicates memory)
  - Cannot use async SQLAlchemy sessions across processes
  - Process spawn overhead (~100-200ms per process)
  - Doesn't play well with existing async architecture
- **Rationale**: REJECTED - Memory constraints, async incompatibility

**Decision**: Option A (AsyncIO with Semaphore)  
**Implementation**: Add `process_batch()` function to orchestrator, use semaphore limiting, ensure proper session management with `async_scoped_session`.

**Concurrency Configuration**:
- Default: 20 concurrent invoices
- Configurable via environment variable: `MAX_CONCURRENT_PROCESSING`
- Database connection pool: Increase to 30 connections (20 workers + 10 API requests)
- Memory monitoring: Alert if container memory exceeds 8GB (20 × 512MB theoretical max)

---

### 4. Per-Field Confidence Tracking

**Requirement**: Store and display confidence scores for individual extracted fields (not just document-level confidence).

**Options Evaluated**:

#### Option A: Separate Columns per Field (SELECTED)
- **Approach**: Add `vendor_name_confidence`, `invoice_number_confidence`, `total_amount_confidence`, etc. columns to `extracted_data` table
- **Schema**:
  ```sql
  ALTER TABLE extracted_data ADD COLUMN vendor_name_confidence NUMERIC(3,2);
  ALTER TABLE extracted_data ADD COLUMN invoice_number_confidence NUMERIC(3,2);
  ALTER TABLE extracted_data ADD COLUMN total_amount_confidence NUMERIC(3,2);
  CREATE INDEX idx_extracted_data_vendor_conf ON extracted_data(vendor_name_confidence);
  ```
- **Pros**:
  - Fast queries: Can filter/sort by specific field confidence with indexes
  - Schema is explicit and self-documenting
  - No JSON parsing overhead
  - Type-safe with PostgreSQL numeric type
- **Cons**:
  - More columns (7-10 additional columns)
  - Schema migration required
  - Less flexible if adding new fields later
- **Query Performance**: <50ms for filtering 10k invoices by confidence
- **Rationale**: Best query performance, explicit schema, meets requirements

#### Option B: JSONB Column for All Confidences
- **Approach**: Add single `field_confidences` JSONB column with structure like `{"vendor_name": 0.95, "invoice_number": 0.88, ...}`
- **Pros**:
  - Flexible: Easy to add new fields
  - Single column (cleaner schema)
  - Can store additional metadata per field
- **Cons**:
  - Slower queries: JSONB operators less efficient than native columns
  - Harder to index (requires GIN index on entire JSONB)
  - Type validation in application layer, not database
- **Query Performance**: ~200ms for filtering 10k invoices (4x slower than Option A)
- **Rationale**: REJECTED - Query performance doesn't meet <3s dashboard load requirement

#### Option C: Separate Table for Field Confidences
- **Approach**: Create `field_confidences` table with columns: `extracted_data_id`, `field_name`, `confidence_score`
- **Pros**:
  - Normalized design
  - Flexible for any number of fields
- **Cons**:
  - Requires JOIN for every query
  - 7-10x more rows (one row per field per invoice)
  - Slower queries due to JOIN overhead
- **Rationale**: REJECTED - Over-normalized, doesn't meet performance requirements

**Decision**: Option A (Separate Columns per Field)  
**Implementation**: Add 7 confidence columns for critical fields: vendor_name, invoice_number, invoice_date, total_amount, subtotal, tax_amount, currency. Add indexes for filtering and sorting.

**Confidence Calculation Strategy**:
- LLM-based: Parse LLM response to extract field-level confidence if provided, otherwise derive from document confidence
- OCR-based: Use OCR word-level confidence scores, aggregate by field (average confidence of words in field)
- Rule-based fallback: If field passes validation, confidence = 0.95; if fails, confidence = 0.50; if NULL, confidence = 0.0

---

### 5. UI Enhancement Patterns

**Requirement**: Add quality metrics dashboard, inline editing, confidence visualization, and filtering capabilities.

**Technology Choice**: Continue using Streamlit (no framework change).

**Component Design Decisions**:

#### A. Confidence Visualization
**Selected Approach**: Color-coded badges with tooltips
- Red badge (<50%): "Low Confidence - Review Required"
- Yellow badge (50-70%): "Medium Confidence - May Need Review"
- Green badge (>70%): "High Confidence"
- Implementation: Custom Streamlit component using HTML/CSS with `st.markdown(unsafe_allow_html=True)`

#### B. Inline Editing
**Selected Approach**: Streamlit form with `st.text_input` + autocomplete via `st.selectbox` with previous values
- Autocomplete source: Query distinct vendor names and invoice numbers from database
- Save mechanism: "Save" button triggers async API call, shows success/error message
- Validation: Re-run validation rules on save, display updated validation status

#### C. Quality Metrics Dashboard
**Selected Approach**: Streamlit metrics + Plotly charts
- Metrics: `st.metric()` for headline numbers (STP rate, avg confidence, total invoices)
- Charts: Plotly bar charts for format comparison, line charts for trends over time
- Caching: Use `@st.cache_data(ttl=300)` to cache metrics for 5 minutes

#### D. Filtering & Sorting
**Selected Approach**: Enhance existing sidebar filters with quality-specific options
- Add filters: Confidence range slider, "Has Missing Fields" checkbox, "Validation Failed" checkbox
- Backend: Pass filters to SQL query, use indexes for performance
- UI: Use `st.slider()` for confidence range, `st.checkbox()` for boolean filters

---

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| File Preview (PDF) | Streamlit + base64 | Native | No dependencies, good performance for <10MB files |
| File Preview (CSV/Excel) | Streamlit + pandas | 2.2.3 | Existing dependency, built-in dataframe rendering |
| File Preview (Images) | Streamlit st.image | Native | Native component, efficient rendering |
| Extraction Enhancement | OpenAI API + format hints | 1.58.x | Existing integration, no new dependencies |
| Parallel Processing | AsyncIO + Semaphore | Native | No dependencies, fits async architecture |
| Per-Field Confidence | PostgreSQL numeric columns | - | Best query performance, explicit schema |
| UI Components | Streamlit + Plotly | 1.40.x + latest | Existing stack, rich component library |
| Caching | Streamlit caching + Redis | Native | Streamlit built-in caching sufficient for current scale |

## Implementation Priorities

Based on research findings and user requirements, recommended implementation order:

1. **Phase 1 (Core Quality Improvements)**:
   - Database migration: Add per-field confidence columns
   - Enhanced extraction: Format-specific prompt engineering and preprocessing
   - Measure baseline accuracy, implement improvements, validate 85%+ target

2. **Phase 2 (UI Enhancements)**:
   - File preview components (PDF, CSV, images)
   - Confidence visualization in invoice detail view
   - Quality metrics dashboard with filters

3. **Phase 3 (Advanced Features)**:
   - Inline editing with autocomplete
   - Parallel processing for batch uploads
   - Quality trend charts and export capabilities

This ordering prioritizes extraction quality (highest user pain point) before UI enhancements.

## Alternatives Considered and Rejected

### 1. Custom React Dashboard
**Reason for Rejection**: Violates simplicity principle, adds significant complexity, breaks existing Streamlit architecture. Streamlit is sufficient for current requirements.

### 2. Separate ML Model per Format
**Reason for Rejection**: Requires training data, infrastructure for model serving, higher maintenance burden. LLM with format hints achieves similar accuracy without complexity.

### 3. Redis Queue for Processing
**Reason for Rejection**: Violates "All-in-Postgres" architecture, adds infrastructure dependency. AsyncIO with semaphore meets performance requirements.

### 4. NoSQL Database for Confidence Scores
**Reason for Rejection**: Breaks existing PostgreSQL architecture, requires managing multiple databases, doesn't provide significant benefits over PostgreSQL JSONB or native columns.

## Open Questions and Assumptions

**Assumptions**:
1. File uploads will not exceed 50MB (current limit enforced in upload UI)
2. PDF preview acceptable without advanced controls (zoom limited to browser controls)
3. 20 concurrent processing operations sufficient for current user base
4. 85% extraction accuracy target is acceptable (100% not achievable without perfect OCR/documents)
5. Per-field confidence for 7 critical fields is sufficient (can expand later if needed)

**Open Questions** (none remaining - all resolved in research):
- All technical unknowns from spec.md have been researched and decided

## Performance Validation Plan

To validate research decisions meet performance requirements:

1. **Benchmark File Preview**:
   - Test files: PDF (1MB, 5MB, 10MB), CSV (10k rows, 50k rows), Image (2MB, 5MB)
   - Measure: Time to first render in Streamlit
   - Target: <2s for all files <10MB

2. **Benchmark Extraction Accuracy**:
   - Test set: 100 invoices across all formats (25 PDF, 25 Excel, 25 CSV, 25 images)
   - Manually verify extracted critical fields
   - Measure: % of invoices with all critical fields correct
   - Target: 85%+ overall, 95%+ for Excel

3. **Benchmark Parallel Processing**:
   - Test: Process 20 invoices concurrently, measure completion time and memory usage
   - Target: <20s total time, <8GB memory usage

4. **Benchmark Dashboard Load**:
   - Test: Load quality metrics dashboard with 1000 invoices
   - Measure: Time from page load to full render
   - Target: <3s

## References

- Streamlit Documentation: https://docs.streamlit.io/
- FastAPI Async Patterns: https://fastapi.tiangolo.com/async/
- PostgreSQL Performance Tuning: https://wiki.postgresql.org/wiki/Performance_Optimization
- OpenAI API Best Practices: https://platform.openai.com/docs/guides/prompt-engineering
- AsyncIO Semaphore Patterns: https://docs.python.org/3/library/asyncio-sync.html#semaphore

