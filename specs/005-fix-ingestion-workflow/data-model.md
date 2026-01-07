# Data Model: Fix Ingestion Workflow

**Feature**: Fix Ingestion Workflow  
**Date**: 2025-01-27

## Overview

This document describes the database schema and data model for the invoice ingestion workflow. The schema uses PostgreSQL with SQLAlchemy 2.0 ORM models.

## Entity Relationships

```
Invoice (1) ──< (1) ExtractedData
Invoice (1) ──< (*) ValidationResult
Invoice (1) ──< (*) ProcessingJob
```

## Entities

### Invoice

Represents an uploaded invoice file with processing metadata.

**Table**: `invoices`

**Key Attributes**:
- `id` (UUID, PK): Unique invoice identifier
- `storage_path` (String, 512): Relative path to file from data directory
- `file_name` (String, 256): Original filename
- `file_hash` (String, 64): SHA-256 hash of file content (indexed)
- `file_size` (BigInteger): File size in bytes
- `file_type` (String, 10): File type (pdf, xlsx, csv, jpg, png, etc.)
- `version` (Integer): Version number for duplicate files (default: 1)
- `processing_status` (String, 20): Status enum (pending, queued, processing, completed, failed)
- `category` (String, 100, nullable, indexed): Logical category (e.g., "Invoice", "Receipt")
- `group` (String, 100, nullable, indexed): Logical group/source (e.g., "grok", "jimeng")
- `job_id` (UUID, nullable, indexed): Associated processing job ID
- `encrypted_file_path` (String, 512, nullable): Path to encrypted file if encryption enabled
- `upload_metadata` (JSONB, nullable): Metadata about upload (subfolder, upload_source, uploaded_at, etc.)
- `created_at` (DateTime, timezone): Record creation timestamp
- `updated_at` (DateTime, timezone): Last update timestamp
- `processed_at` (DateTime, timezone, nullable): Processing completion timestamp
- `error_message` (Text, nullable): Error message if processing failed

**Indexes**:
- `idx_invoices_status`: `processing_status`
- `idx_invoices_created_at`: `created_at`
- `ix_invoices_category`: `category`
- `ix_invoices_file_hash`: `file_hash`
- `ix_invoices_group`: `group`
- `ix_invoices_job_id`: `job_id`

**Constraints**:
- `check_file_hash_format`: File hash must be 64-character hex string
- `check_file_type`: File type must be in allowed list
- `check_version_positive`: Version must be >= 1

**State Transitions**:
```
pending → queued → processing → completed
                              ↓
                           failed
```

### ExtractedData

Contains structured invoice data extracted from files.

**Table**: `extracted_data`

**Key Attributes**:
- `id` (UUID, PK): Unique extracted data identifier
- `invoice_id` (UUID, FK → invoices.id, unique): Associated invoice (one-to-one)
- `vendor_name` (String, 256, nullable, indexed): Vendor/supplier name
- `invoice_number` (String, 100, nullable): Invoice number
- `invoice_date` (Date, nullable, indexed): Invoice date
- `due_date` (Date, nullable): Payment due date
- `subtotal` (Numeric(15,2), nullable): Subtotal amount
- `tax_amount` (Numeric(15,2), nullable): Tax amount
- `tax_rate` (Numeric(5,4), nullable): Tax rate (0.0-1.0)
- `total_amount` (Numeric(15,2), nullable, indexed): Total amount
- `currency` (String, 3, nullable, default: "USD"): Currency code
- `line_items` (JSONB, nullable): Line items as JSON array
- `raw_text` (Text, nullable): Raw extracted text
- `extraction_confidence` (Numeric(3,2), nullable, indexed): Confidence score (0.0-1.0)
- `extracted_at` (DateTime, timezone): Extraction timestamp

**Indexes**:
- `idx_extracted_data_vendor`: `vendor_name`
- `idx_extracted_data_date`: `invoice_date`
- `idx_extracted_data_total_amount`: `total_amount`
- `idx_extracted_data_confidence`: `extraction_confidence`

**Constraints**:
- `check_subtotal_non_negative`: Subtotal >= 0 if not null
- `check_tax_non_negative`: Tax amount >= 0 if not null
- `check_total_non_negative`: Total amount >= 0 if not null
- `check_tax_rate_range`: Tax rate between 0.0 and 1.0 if not null
- `check_confidence_range`: Confidence between 0.0 and 1.0 if not null

### ValidationResult

Stores results of business rule validation checks.

**Table**: `validation_results`

**Key Attributes**:
- `id` (UUID, PK): Unique validation result identifier
- `invoice_id` (UUID, FK → invoices.id): Associated invoice (one-to-many)
- `rule_name` (String, 100, indexed): Validation rule name
- `rule_description` (Text, nullable): Rule description
- `status` (String, 20): Validation status enum (passed, failed, warning)
- `expected_value` (Numeric(15,2), nullable): Expected value for comparison
- `actual_value` (Numeric(15,2), nullable): Actual value from extraction
- `tolerance` (Numeric(10,4), nullable): Allowed tolerance for comparison
- `error_message` (Text, nullable): Error message if validation failed
- `validated_at` (DateTime, timezone): Validation timestamp

**Indexes**:
- `idx_validation_results_invoice_id`: `invoice_id`
- `idx_validation_results_status`: `status`
- `idx_validation_results_rule`: `rule_name`

### ProcessingJob

Tracks background processing tasks.

**Table**: `processing_jobs`

**Key Attributes**:
- `id` (UUID, PK): Unique job identifier
- `invoice_id` (UUID, FK → invoices.id): Associated invoice (one-to-many)
- `job_type` (String, 50, indexed): Job type enum (file_ingestion, ocr_processing, data_extraction, validation)
- `execution_type` (String, 20): Execution type enum (async_coroutine, cpu_process)
- `status` (String, 20, indexed): Processing status enum (pending, queued, processing, completed, failed)
- `worker_id` (String, 100, nullable): Worker identifier
- `started_at` (DateTime, timezone, nullable): Job start timestamp
- `completed_at` (DateTime, timezone, nullable): Job completion timestamp
- `error_message` (Text, nullable): Error message if job failed
- `error_traceback` (Text, nullable): Full error traceback
- `retry_count` (Integer, default: 0): Number of retry attempts
- `job_metadata` (JSONB, nullable): Additional job metadata

**Indexes**:
- `idx_processing_jobs_invoice_id`: `invoice_id`
- `idx_processing_jobs_status`: `status`
- `idx_processing_jobs_type`: `job_type`

**Constraints**:
- `check_retry_count_non_negative`: Retry count >= 0

## Schema Migration History

1. **001_initial**: Initial schema with `file_path` column
2. **002_dashboard_indexes**: Added indexes for dashboard queries
3. **003_upload_metadata**: Added `upload_metadata` JSONB column
4. **8c2b9c709184**: Refactored to use `storage_path` instead of `file_path`, added `category`, `group`, `job_id` columns

## Current Schema Issues

- Migration `8c2b9c709184` may not be applied to all databases
- Need to verify schema matches code models before processing
- Missing error handling for schema mismatch scenarios

## Validation Rules

Business rules validated in `ValidationResult`:
- `math_check_subtotal_tax`: Subtotal + tax = total
- `line_item_math`: Line items sum = subtotal
- `vendor_sanity`: Vendor name exists
- `date_consistency`: Due date >= invoice date

