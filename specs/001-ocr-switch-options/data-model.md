# Data Model: Switchable OCR Providers

## Entities

### OCR Provider

**Purpose**: Represents an available OCR engine and its runtime availability.  
**Fields**:
- `provider_id` (string, unique)
- `name` (string, human-readable)
- `is_enabled` (boolean)
- `is_default` (boolean)
- `status` (string: `available` | `unavailable`)
- `supported_formats` (list of strings)
- `updated_at` (datetime)

### OCR Result

**Purpose**: Stores extracted data for a single input using a specific provider.  
**Fields**:
- `result_id` (string, unique)
- `input_id` (string, references Source Document/Invoice)
- `provider_id` (string, references OCR Provider)
- `extracted_text` (string)
- `extracted_fields` (object/map)
- `status` (string: `success` | `failed`)
- `error_message` (string, optional)
- `duration_ms` (integer)
- `created_at` (datetime)

### OCR Comparison

**Purpose**: Links two OCR results for the same input to support side-by-side review.  
**Fields**:
- `comparison_id` (string, unique)
- `input_id` (string, references Source Document/Invoice)
- `provider_a_result_id` (string, references OCR Result)
- `provider_b_result_id` (string, references OCR Result)
- `summary` (string, optional)
- `created_at` (datetime)

## Relationships

- `OCR Result` → `OCR Provider` (many-to-one)
- `OCR Comparison` → `OCR Result` (two results per comparison)
- `OCR Result` → `Source Document/Invoice` (many-to-one, existing entity)

## Validation Rules

- Only one provider can be marked as `is_default` at any time.
- `provider_a_result_id` and `provider_b_result_id` must reference distinct providers.
- Comparisons are limited to a single input per request.
- If a provider fails, its `OCR Result.status` is `failed` with `error_message` populated.
