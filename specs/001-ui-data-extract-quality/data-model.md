# Data Model: UI and Multi-Format Data Extraction Quality Improvements

**Feature**: UI and Multi-Format Data Extraction Quality  
**Date**: January 7, 2026  
**Branch**: `001-ui-data-extract-quality`

## Overview

This document describes the database schema changes required to support per-field confidence tracking, file preview caching, and parallel processing metadata. The changes are additive and backward-compatible with existing data.

## Schema Changes Summary

| Table | Change Type | Description |
|-------|------------|-------------|
| `extracted_data` | ADD COLUMNS | Add per-field confidence scores (7 columns) |
| `invoices` | ADD COLUMN | Add file preview metadata cache (JSONB) |
| `invoices` | ADD COLUMN | Add processing metadata for parallel operations (JSONB) |
| - | ADD INDEXES | Add indexes on confidence columns for filtering/sorting |

## Modified Entities

### ExtractedData (Modified)

**Table**: `extracted_data`

**New Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `vendor_name_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for vendor name extraction (0.0-1.0) |
| `invoice_number_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for invoice number extraction (0.0-1.0) |
| `invoice_date_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for invoice date extraction (0.0-1.0) |
| `total_amount_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for total amount extraction (0.0-1.0) |
| `subtotal_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for subtotal extraction (0.0-1.0) |
| `tax_amount_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for tax amount extraction (0.0-1.0) |
| `currency_confidence` | NUMERIC(3,2) | NULL, CHECK >= 0.0 AND <= 1.0 | Confidence score for currency extraction (0.0-1.0) |

**New Indexes**:

| Index Name | Columns | Purpose |
|------------|---------|---------|
| `idx_extracted_data_vendor_conf` | `vendor_name_confidence` | Filter/sort by vendor name confidence |
| `idx_extracted_data_invoice_num_conf` | `invoice_number_confidence` | Filter/sort by invoice number confidence |
| `idx_extracted_data_total_conf` | `total_amount_confidence` | Filter/sort by total amount confidence |
| `idx_extracted_data_low_confidence` | `COALESCE(vendor_name_confidence, 0) + COALESCE(invoice_number_confidence, 0) + COALESCE(total_amount_confidence, 0)` | Filter invoices with overall low confidence (expression index) |

**Complete Schema** (existing + new columns):

```sql
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY,
    invoice_id UUID NOT NULL UNIQUE REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Extracted fields (existing)
    vendor_name VARCHAR(256) NULL,
    invoice_number VARCHAR(100) NULL,
    invoice_date DATE NULL,
    due_date DATE NULL,
    subtotal NUMERIC(15,2) NULL,
    tax_amount NUMERIC(15,2) NULL,
    tax_rate NUMERIC(5,4) NULL,
    total_amount NUMERIC(15,2) NULL,
    currency VARCHAR(3) NULL DEFAULT 'USD',
    line_items JSONB NULL,
    raw_text TEXT NULL,
    extraction_confidence NUMERIC(3,2) NULL,
    extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- NEW: Per-field confidence scores
    vendor_name_confidence NUMERIC(3,2) NULL,
    invoice_number_confidence NUMERIC(3,2) NULL,
    invoice_date_confidence NUMERIC(3,2) NULL,
    total_amount_confidence NUMERIC(3,2) NULL,
    subtotal_confidence NUMERIC(3,2) NULL,
    tax_amount_confidence NUMERIC(3,2) NULL,
    currency_confidence NUMERIC(3,2) NULL,
    
    -- Constraints
    CONSTRAINT check_subtotal_non_negative CHECK (subtotal IS NULL OR subtotal >= 0),
    CONSTRAINT check_tax_non_negative CHECK (tax_amount IS NULL OR tax_amount >= 0),
    CONSTRAINT check_total_non_negative CHECK (total_amount IS NULL OR total_amount >= 0),
    CONSTRAINT check_tax_rate_range CHECK (tax_rate IS NULL OR (tax_rate >= 0 AND tax_rate <= 1)),
    CONSTRAINT check_confidence_range CHECK (extraction_confidence IS NULL OR (extraction_confidence >= 0 AND extraction_confidence <= 1)),
    
    -- NEW: Per-field confidence constraints
    CONSTRAINT check_vendor_conf_range CHECK (vendor_name_confidence IS NULL OR (vendor_name_confidence >= 0 AND vendor_name_confidence <= 1)),
    CONSTRAINT check_invoice_num_conf_range CHECK (invoice_number_confidence IS NULL OR (invoice_number_confidence >= 0 AND invoice_number_confidence <= 1)),
    CONSTRAINT check_invoice_date_conf_range CHECK (invoice_date_confidence IS NULL OR (invoice_date_confidence >= 0 AND invoice_date_confidence <= 1)),
    CONSTRAINT check_total_conf_range CHECK (total_amount_confidence IS NULL OR (total_amount_confidence >= 0 AND total_amount_confidence <= 1)),
    CONSTRAINT check_subtotal_conf_range CHECK (subtotal_confidence IS NULL OR (subtotal_confidence >= 0 AND subtotal_confidence <= 1)),
    CONSTRAINT check_tax_conf_range CHECK (tax_amount_confidence IS NULL OR (tax_amount_confidence >= 0 AND tax_amount_confidence <= 1)),
    CONSTRAINT check_currency_conf_range CHECK (currency_confidence IS NULL OR (currency_confidence >= 0 AND currency_confidence <= 1))
);

-- Existing indexes
CREATE INDEX idx_extracted_data_invoice_id ON extracted_data(invoice_id);
CREATE INDEX idx_extracted_data_vendor ON extracted_data(vendor_name);
CREATE INDEX idx_extracted_data_date ON extracted_data(invoice_date);
CREATE INDEX idx_extracted_data_total_amount ON extracted_data(total_amount);
CREATE INDEX idx_extracted_data_confidence ON extracted_data(extraction_confidence);

-- NEW: Confidence indexes for filtering
CREATE INDEX idx_extracted_data_vendor_conf ON extracted_data(vendor_name_confidence);
CREATE INDEX idx_extracted_data_invoice_num_conf ON extracted_data(invoice_number_confidence);
CREATE INDEX idx_extracted_data_total_conf ON extracted_data(total_amount_confidence);

-- NEW: Expression index for low-confidence filtering
CREATE INDEX idx_extracted_data_low_confidence ON extracted_data(
    (COALESCE(vendor_name_confidence, 0) + COALESCE(invoice_number_confidence, 0) + COALESCE(total_amount_confidence, 0))
);
```

**Confidence Calculation Logic**:

Confidence scores are calculated during extraction using the following strategy:

1. **LLM-Based Extraction**:
   - If LLM provides per-field confidence in response: Use provided confidence
   - If LLM only provides document-level confidence: Use document confidence for all fields with values, 0.0 for NULL fields
   - If LLM provides no confidence: Calculate based on validation results (see below)

2. **Validation-Based Confidence**:
   - Field extracted AND passes validation: 0.95
   - Field extracted BUT fails validation: 0.60
   - Field is NULL: 0.0

3. **OCR-Based Confidence** (for image/scanned PDFs):
   - Use OCR word-level confidence scores
   - Aggregate confidence = average of confidence scores for words in the field
   - Example: "ACME Corp" extracted with word confidences [0.98, 0.92] → vendor_name_confidence = 0.95

**Data Integrity Rules**:

- If field value is NULL, confidence SHOULD be 0.0 (enforced in application, not database)
- If field value is NOT NULL, confidence SHOULD be > 0.0 (enforced in application)
- Document-level `extraction_confidence` SHOULD equal average of per-field confidences (calculated field, not enforced)

---

### Invoice (Modified)

**Table**: `invoices`

**New Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `file_preview_metadata` | JSONB | NULL | Cached file preview data (file size, page count for PDFs, row count for CSV, image dimensions) |
| `processing_metadata` | JSONB | NULL | Metadata about processing execution (duration, retry count, parallel batch ID, format-specific settings) |

**Example `file_preview_metadata` Structure**:

```json
{
  "file_size_bytes": 2458624,
  "preview_generated_at": "2026-01-07T10:30:00Z",
  "pdf": {
    "page_count": 3,
    "has_text_layer": true,
    "preview_mode": "embedded"
  },
  "csv": {
    "row_count": 1523,
    "column_count": 12,
    "has_headers": true,
    "delimiter": ",",
    "encoding": "utf-8"
  },
  "image": {
    "width": 2480,
    "height": 3508,
    "format": "JPEG",
    "dpi": 300
  }
}
```

**Example `processing_metadata` Structure**:

```json
{
  "processing_duration_seconds": 12.4,
  "extraction_duration_seconds": 8.2,
  "validation_duration_seconds": 0.3,
  "retry_count": 0,
  "parallel_batch_id": "batch-2026-01-07-001",
  "concurrent_slot": 5,
  "format_specific": {
    "excel_column_mapping": {
      "Vendor": "vendor_name",
      "Invoice #": "invoice_number",
      "Total": "total_amount"
    },
    "pdf_extraction_method": "text",
    "image_preprocessing_applied": ["contrast_enhancement", "noise_reduction"]
  },
  "llm_tokens_used": 1250,
  "llm_model": "deepseek-chat"
}
```

**Schema Addition**:

```sql
-- Add new columns to invoices table
ALTER TABLE invoices ADD COLUMN file_preview_metadata JSONB NULL;
ALTER TABLE invoices ADD COLUMN processing_metadata JSONB NULL;

-- Index for querying by batch ID (useful for monitoring parallel processing)
CREATE INDEX idx_invoices_batch_id ON invoices((processing_metadata->>'parallel_batch_id'));
```

---

## New Computed Fields (Application Layer)

These are not stored in the database but calculated on-demand in queries or application logic:

### Quality Metrics (Computed)

**Purpose**: Provide aggregated quality statistics for dashboard

**Calculation**:

```sql
-- Overall extraction quality score (0-100%)
WITH field_scores AS (
    SELECT 
        invoice_id,
        COALESCE(vendor_name_confidence, 0) AS vendor_score,
        COALESCE(invoice_number_confidence, 0) AS invoice_num_score,
        COALESCE(total_amount_confidence, 0) AS total_score
    FROM extracted_data
)
SELECT 
    invoice_id,
    ((vendor_score + invoice_num_score + total_score) / 3.0) * 100 AS quality_score
FROM field_scores;

-- Critical fields completeness (0-100%)
SELECT 
    invoice_id,
    ((CASE WHEN vendor_name IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN invoice_number IS NOT NULL THEN 1 ELSE 0 END +
      CASE WHEN total_amount IS NOT NULL THEN 1 ELSE 0 END) / 3.0) * 100 AS completeness_pct
FROM extracted_data;

-- Invoices requiring review (low confidence or missing critical fields)
SELECT 
    i.id,
    i.file_name,
    COALESCE(e.vendor_name_confidence, 0) AS vendor_conf,
    COALESCE(e.invoice_number_confidence, 0) AS invoice_num_conf,
    COALESCE(e.total_amount_confidence, 0) AS total_conf
FROM invoices i
LEFT JOIN extracted_data e ON i.id = e.invoice_id
WHERE 
    e.vendor_name IS NULL 
    OR e.invoice_number IS NULL 
    OR e.total_amount IS NULL
    OR COALESCE(e.vendor_name_confidence, 0) < 0.7
    OR COALESCE(e.invoice_number_confidence, 0) < 0.7
    OR COALESCE(e.total_amount_confidence, 0) < 0.7;
```

### Format-Specific Accuracy (Computed)

**Purpose**: Compare extraction accuracy across file formats

**Calculation**:

```sql
-- Accuracy by file format
SELECT 
    i.file_type,
    COUNT(*) AS total_invoices,
    SUM(CASE WHEN e.vendor_name IS NOT NULL THEN 1 ELSE 0 END) AS vendor_extracted,
    SUM(CASE WHEN e.invoice_number IS NOT NULL THEN 1 ELSE 0 END) AS invoice_num_extracted,
    SUM(CASE WHEN e.total_amount IS NOT NULL THEN 1 ELSE 0 END) AS total_extracted,
    AVG(COALESCE(e.vendor_name_confidence, 0)) AS avg_vendor_conf,
    AVG(COALESCE(e.invoice_number_confidence, 0)) AS avg_invoice_num_conf,
    AVG(COALESCE(e.total_amount_confidence, 0)) AS avg_total_conf
FROM invoices i
LEFT JOIN extracted_data e ON i.id = e.invoice_id
WHERE i.processing_status = 'completed'
GROUP BY i.file_type
ORDER BY total_invoices DESC;
```

---

## Migration Strategy

### Migration File: `002_add_field_confidence.py`

**Filename**: `alembic/versions/002_add_per_field_confidence.py`

**Operations**:

1. Add 7 confidence columns to `extracted_data` table
2. Add `file_preview_metadata` and `processing_metadata` to `invoices` table
3. Create 4 new indexes
4. Add CHECK constraints for confidence ranges
5. Backfill confidence scores for existing records (optional, can be done later)

**Downgrade Strategy**:
- Drop columns and indexes
- Data loss acceptable (confidence scores are derived, not source data)

**Estimated Migration Time**:
- For 10k invoices: ~5 seconds (column additions are instant in PostgreSQL, indexes take 1-2s)
- For 100k invoices: ~30 seconds

**Backward Compatibility**:
- New columns are nullable, so existing code continues to work
- Existing queries unaffected (don't reference new columns)
- Application code should handle NULL confidences gracefully

### Backfill Strategy (Optional)

For existing invoices without per-field confidence scores:

**Option 1: Lazy Backfill** (RECOMMENDED)
- Leave existing invoices with NULL confidence scores
- Calculate and populate confidence scores on-demand when invoice is viewed in dashboard
- Display "Confidence Unknown" badge for NULL confidence fields
- Pros: Fast migration, no reprocessing required
- Cons: Inconsistent data until invoices are viewed

**Option 2: Batch Reprocessing**
- Re-run extraction for all existing invoices to populate confidence scores
- Use parallel processing to speed up reprocessing (process in batches of 20)
- Pros: All data consistent immediately
- Cons: Expensive (LLM API calls), time-consuming (hours for thousands of invoices)

**Option 3: Rule-Based Backfill**
- Use validation results to infer confidence scores:
  - If field is NOT NULL and validation passed: confidence = 0.95
  - If field is NOT NULL and validation failed: confidence = 0.60
  - If field is NULL: confidence = 0.0
- Run as SQL UPDATE statement
- Pros: Fast, no LLM calls, reasonable approximation
- Cons: Less accurate than actual extraction confidence

**Recommended Approach**: Option 1 (Lazy Backfill) for MVP, Option 3 (Rule-Based) if full historical data needed

---

## Query Performance Analysis

### Expected Query Patterns

1. **Filter by low confidence** (Quality Dashboard):
   ```sql
   SELECT * FROM invoices i
   JOIN extracted_data e ON i.id = e.invoice_id
   WHERE e.vendor_name_confidence < 0.7
      OR e.invoice_number_confidence < 0.7
      OR e.total_amount_confidence < 0.7;
   ```
   **Performance**: Uses `idx_extracted_data_vendor_conf`, `idx_extracted_data_invoice_num_conf`, `idx_extracted_data_total_conf` indexes. Expected: <100ms for 10k invoices.

2. **Aggregate quality metrics** (Dashboard Header):
   ```sql
   SELECT 
       COUNT(*) AS total,
       AVG(e.vendor_name_confidence) AS avg_vendor_conf,
       SUM(CASE WHEN e.vendor_name IS NULL THEN 1 ELSE 0 END) AS missing_vendor
   FROM invoices i
   LEFT JOIN extracted_data e ON i.id = e.invoice_id
   WHERE i.processing_status = 'completed';
   ```
   **Performance**: Sequential scan acceptable (aggregation query). Expected: <500ms for 10k invoices, <3s for 100k invoices.

3. **Sort by confidence** (Invoice List):
   ```sql
   SELECT * FROM invoices i
   JOIN extracted_data e ON i.id = e.invoice_id
   ORDER BY e.vendor_name_confidence DESC
   LIMIT 50;
   ```
   **Performance**: Uses `idx_extracted_data_vendor_conf` index for sorting. Expected: <50ms for 10k invoices.

### Index Usage Verification

After migration, verify indexes are being used:

```sql
EXPLAIN ANALYZE
SELECT * FROM extracted_data
WHERE vendor_name_confidence < 0.7;
```

Expected output: `Index Scan using idx_extracted_data_vendor_conf on extracted_data`

---

## Data Validation Rules

### Application-Level Validation

These rules are enforced in the application layer (Pydantic models, business logic):

1. **Confidence-Value Consistency**:
   - If field value is NULL, confidence SHOULD be 0.0 (warning logged if not)
   - If field value is NOT NULL, confidence SHOULD be > 0.0 (warning logged if not)

2. **Confidence Range**:
   - All confidence scores MUST be between 0.0 and 1.0 (enforced by database CHECK constraint)

3. **Document Confidence Calculation**:
   - `extraction_confidence` SHOULD equal average of non-NULL per-field confidences
   - Recalculated when per-field confidences are updated

4. **Preview Metadata Validation**:
   - `file_preview_metadata` must be valid JSON
   - File size in metadata should match actual file size (warning if mismatch)

### Database-Level Constraints

Already covered in schema definition above (CHECK constraints).

---

## Entity Relationships

No changes to entity relationships. All modifications are adding attributes to existing entities.

```
Invoice (1) ──< (1) ExtractedData  [UNCHANGED]
Invoice (1) ──< (*) ValidationResult  [UNCHANGED]
Invoice (1) ──< (*) ProcessingJob  [UNCHANGED, if exists]
```

---

## Storage Requirements

### Estimated Storage Impact

Assuming 10,000 invoices:

**Per-field confidence columns** (7 columns × NUMERIC(3,2) × 10,000 rows):
- NUMERIC(3,2) = 5 bytes per value
- 7 columns × 5 bytes × 10,000 = 350 KB (negligible)

**Indexes on confidence columns** (4 indexes):
- ~8 bytes per entry × 10,000 rows × 4 indexes = 320 KB

**JSONB columns** (`file_preview_metadata`, `processing_metadata`):
- Average size: 500 bytes per invoice (estimated)
- 2 columns × 500 bytes × 10,000 = 10 MB

**Total storage impact**: ~11 MB for 10,000 invoices (negligible)

**Scaling**: For 1 million invoices, total impact is ~1.1 GB (still manageable)

---

## Future Extensibility

### Potential Future Enhancements

1. **Additional Confidence Fields**:
   - Add confidence for `due_date`, `line_items`, `tax_rate` if needed
   - Follow same pattern: add column with CHECK constraint, add index

2. **Confidence History Tracking**:
   - Create separate `confidence_history` table to track confidence changes over time
   - Useful for analyzing extraction improvement after model updates

3. **Multi-Model Confidence**:
   - Store confidence from multiple extraction models (e.g., GPT-4, DeepSeek, custom model)
   - Use separate columns: `vendor_name_confidence_gpt4`, `vendor_name_confidence_deepseek`
   - Compare and use ensemble/voting strategy

4. **Field-Level Correction Tracking**:
   - Track which fields were manually corrected by users
   - Add `vendor_name_corrected_by`, `vendor_name_corrected_at` columns
   - Use for extraction model fine-tuning

---

## Summary of Changes

| Change | Impact | Risk | Mitigation |
|--------|--------|------|-----------|
| Add 7 confidence columns | Enables per-field filtering/sorting | Low | Columns nullable, backward compatible |
| Add confidence indexes | Improves query performance | Low | Standard B-tree indexes, tested pattern |
| Add JSONB metadata columns | Enables caching and analytics | Low | JSONB efficient in PostgreSQL, nullable |
| Expression index for low confidence | Optimizes quality dashboard query | Medium | Test query performance before/after |
| Backfill existing data | Provides consistent historical data | Medium | Use lazy or rule-based backfill |

All changes are additive and backward-compatible. Rollback is straightforward (drop columns and indexes).

