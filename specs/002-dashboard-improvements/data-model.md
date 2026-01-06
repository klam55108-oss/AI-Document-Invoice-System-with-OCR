# Data Model: Dashboard Improvements

**Created**: 2025-01-27  
**Purpose**: Define data structures, filter state, export requests, and bulk action models for dashboard improvements

## Overview

This feature extends the existing dashboard with new UI components and utilities. The core data models (Invoice, ExtractedData, ValidationResult) remain unchanged. New data structures are introduced for filter state, export requests, and bulk actions.

## Existing Entities (No Changes)

### Invoice
- **Table**: `invoices`
- **Key Fields**: `id`, `storage_path`, `file_name`, `file_hash`, `file_type`, `version`, `processing_status`, `created_at`, `processed_at`, `category`, `group`, `job_id`
- **Relationships**: One-to-one with ExtractedData, one-to-many with ValidationResult

### ExtractedData
- **Table**: `extracted_data`
- **Key Fields**: `vendor_name`, `invoice_number`, `invoice_date`, `subtotal`, `tax_amount`, `tax_rate`, `total_amount`, `currency`, `line_items`, `extraction_confidence`
- **Note**: All financial fields are nullable (NULL indicates missing data, not zero)

### ValidationResult
- **Table**: `validation_results`
- **Key Fields**: `rule_name`, `rule_description`, `status` (passed/failed/warning), `expected_value`, `actual_value`, `tolerance`, `error_message`

## New Data Structures

### FilterState (Session State)

**Purpose**: Represents the current filter configuration in the dashboard

**Structure**:
```python
{
    "status": ProcessingStatus | None,           # Processing status filter
    "search_query": str | None,                  # Text search (file name, vendor)
    "date_range": tuple[date, date] | None,     # Start and end dates
    "vendor": str | None,                        # Vendor name filter
    "amount_min": Decimal | None,                # Minimum amount filter
    "amount_max": Decimal | None,                # Maximum amount filter
    "confidence_min": Decimal | None,            # Minimum confidence threshold (0-1)
    "validation_status": str | None,             # "passed", "failed", "warning", or None
}
```

**Persistence**: Stored in Streamlit session state, persists during user session

**Validation Rules**:
- `amount_min` must be <= `amount_max` if both provided
- `confidence_min` must be between 0 and 1
- `date_range` start must be <= end date

### ExportRequest (In-Memory)

**Purpose**: Represents a user request to export data

**Structure**:
```python
{
    "format": str,                    # "csv" or "pdf"
    "scope": str,                     # "list" (filtered invoices) or "detail" (single invoice)
    "invoice_ids": list[UUID] | None, # For list export: selected invoice IDs
    "invoice_id": UUID | None,        # For detail export: single invoice ID
    "columns": list[str] | None,      # Optional: specific columns to include (CSV only)
}
```

**Validation Rules**:
- `format` must be "csv" or "pdf"
- `scope` must be "list" or "detail"
- For "list" scope: `invoice_ids` must be provided and non-empty
- For "detail" scope: `invoice_id` must be provided

### BulkAction (In-Memory)

**Purpose**: Represents a bulk operation request

**Structure**:
```python
{
    "action_type": str,                # "reprocess", "delete", "mark_for_review"
    "invoice_ids": list[UUID],        # Target invoice IDs (max 100)
    "options": dict | None,            # Action-specific options
}
```

**Validation Rules**:
- `action_type` must be one of: "reprocess", "delete", "mark_for_review"
- `invoice_ids` must be non-empty and contain at most 100 IDs
- All invoice IDs must be valid UUIDs

**Action-Specific Options**:
- `reprocess`: `{"force": bool}` - Force reprocessing (reset version)
- `delete`: No additional options
- `mark_for_review`: `{"reason": str}` - Optional reason for review

### ChartData (In-Memory)

**Purpose**: Aggregated data for chart visualization

**Structure**:
```python
{
    "chart_type": str,                 # "status_distribution", "time_series", "vendor_analysis", "financial_summary"
    "data": list[dict],                # Chart-specific data points
    "metadata": dict,                   # Chart metadata (title, labels, etc.)
}
```

**Chart-Specific Data Formats**:

1. **Status Distribution**:
```python
{
    "data": [
        {"status": "completed", "count": 150},
        {"status": "failed", "count": 10},
        {"status": "processing", "count": 5},
    ]
}
```

2. **Time Series**:
```python
{
    "data": [
        {"date": "2025-01-01", "count": 25},
        {"date": "2025-01-02", "count": 30},
    ],
    "metadata": {"aggregation": "daily"}  # or "weekly", "monthly"
}
```

3. **Vendor Analysis**:
```python
{
    "data": [
        {"vendor": "Vendor A", "invoice_count": 50, "total_amount": 100000.00},
        {"vendor": "Vendor B", "invoice_count": 30, "total_amount": 75000.00},
    ],
    "metadata": {"sort_by": "count"}  # or "amount"
}
```

4. **Financial Summary**:
```python
{
    "data": {
        "total_amount": 500000.00,
        "tax_breakdown": [
            {"rate": 0.10, "amount": 50000.00},
            {"rate": 0.20, "amount": 30000.00},
        ],
        "currency_distribution": [
            {"currency": "USD", "count": 100},
            {"currency": "EUR", "count": 20},
        ],
    }
}
```

## File Path Resolution

### ResolvedFileInfo

**Purpose**: Result of file path resolution attempt

**Structure**:
```python
{
    "original_path": str,              # Path from database
    "resolved_path": Path | None,      # Resolved absolute path (if found)
    "exists": bool,                    # Whether file exists
    "location": str | None,            # "original", "encrypted", or None
    "error": str | None,               # Error message if resolution failed
}
```

**Resolution Strategy**:
1. Try resolving relative path from `data/` directory
2. If not found, try `data/encrypted/` directory with hash-based filename
3. Return error if neither location found

## Missing Data Indicators

### MissingDataInfo

**Purpose**: Information about missing data fields

**Structure**:
```python
{
    "field_name": str,                 # Field name (e.g., "subtotal")
    "is_missing": bool,                # Whether field is missing
    "reason": str | None,               # Explanation (e.g., "Not found in invoice")
    "confidence": Decimal | None,      # Extraction confidence if available
    "alternative_value": Any | None,   # Alternative value if applicable
}
```

**Standard Reasons**:
- "Not found in invoice" - Field not present in source document
- "Extraction failed" - Extraction process couldn't identify field
- "Low confidence" - Extracted but confidence below threshold
- "Not applicable" - Field doesn't apply to this invoice type

## Validation Display Enhancement

### EnhancedValidationResult

**Purpose**: Enhanced validation result with display metadata

**Structure**:
```python
{
    # Original ValidationResult fields
    "rule_name": str,
    "rule_description": str | None,
    "status": str,                     # "passed", "failed", "warning"
    "expected_value": Decimal | None,
    "actual_value": Decimal | None,
    "tolerance": Decimal | None,
    "error_message": str | None,
    
    # Enhanced fields
    "severity": str,                   # "error", "warning", "info"
    "actionable": bool,                # Whether user can take action
    "suggested_action": str | None,    # Suggested fix (e.g., "Reprocess invoice")
    "display_priority": int,           # Sort order (lower = higher priority)
}
```

**Display Priority**:
- Failed validations: priority 1
- Warnings: priority 2
- Passed validations: priority 3

## Data Aggregation Queries

### Aggregation Functions

**Purpose**: Pre-aggregate data for charts to improve performance

**Query Patterns**:

1. **Status Distribution**:
```sql
SELECT processing_status, COUNT(*) as count
FROM invoices
GROUP BY processing_status
```

2. **Time Series** (daily):
```sql
SELECT DATE(created_at) as date, COUNT(*) as count
FROM invoices
WHERE created_at >= :start_date AND created_at <= :end_date
GROUP BY DATE(created_at)
ORDER BY date
```

3. **Vendor Analysis**:
```sql
SELECT 
    ed.vendor_name,
    COUNT(DISTINCT i.id) as invoice_count,
    SUM(ed.total_amount) as total_amount
FROM invoices i
JOIN extracted_data ed ON i.id = ed.invoice_id
WHERE ed.vendor_name IS NOT NULL
GROUP BY ed.vendor_name
ORDER BY invoice_count DESC
LIMIT 10
```

4. **Financial Summary**:
```sql
SELECT 
    SUM(ed.total_amount) as total_amount,
    SUM(ed.tax_amount) as total_tax,
    COUNT(DISTINCT ed.currency) as currency_count
FROM invoices i
JOIN extracted_data ed ON i.id = ed.invoice_id
WHERE i.processing_status = 'completed'
```

## Indexes for Performance

**New Indexes** (if not already present):
- `idx_extracted_data_vendor` on `extracted_data.vendor_name`
- `idx_extracted_data_total_amount` on `extracted_data.total_amount`
- `idx_extracted_data_confidence` on `extracted_data.extraction_confidence`
- `idx_invoices_created_at` on `invoices.created_at`

## State Transitions

### Filter State
- **Initial**: All filters None/empty
- **User applies filter**: Filter value set in session state
- **User removes filter**: Filter value set to None
- **User resets all**: All filters reset to initial state

### Export Request
- **Created**: User initiates export
- **Processing**: Export generation in progress
- **Completed**: Export file ready for download
- **Failed**: Export generation failed (error message shown)

### Bulk Action
- **Created**: User initiates bulk action
- **Queued**: Actions queued for processing
- **Processing**: Actions being executed
- **Completed**: All actions completed (success/failure summary shown)
- **Failed**: Bulk action failed (error message shown)

