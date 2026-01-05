# Duplicate Processing Logic

## Overview

When you process the same image file multiple times, the system uses **file content hashing** and **versioning** to track reprocessing while maintaining a complete history.

## How It Works

### 1. File Hash Calculation

Every time a file is processed, the system calculates a **SHA-256 hash** of the file's content:

```52:53:ingestion/orchestrator.py
    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
```

The hash is calculated from the actual file content (not filename), so:
- Same file content = Same hash (even if filename differs)
- Different file content = Different hash (even if filename is the same)

### 2. Duplicate Detection

The system checks if an invoice with the same hash already exists:

```57:62:ingestion/orchestrator.py
    # Check for existing invoice with same hash
    from sqlalchemy import select

    existing_invoice_stmt = select(Invoice).where(Invoice.file_hash == file_hash)
    result = await session.execute(existing_invoice_stmt)
    existing_invoice = result.scalar_one_or_none()
```

### 3. Version Management

**If the same file is processed again:**

```64:69:ingestion/orchestrator.py
    # Determine version
    if existing_invoice and not force_reprocess:
        version = existing_invoice.version + 1
        logger.info("Reprocessing existing file", hash=file_hash[:8], version=version)
    else:
        version = 1
```

**Behavior:**
- **First time processing**: Creates new invoice with `version = 1`
- **Same file processed again** (without `force_reprocess`): 
  - Finds the **latest** existing invoice with that hash
  - Increments version: `version = existing_invoice.version + 1`
  - Creates a **NEW invoice record** (new UUID) with the incremented version
- **With `force_reprocess=True`**: Always starts with `version = 1`

### 4. Always Creates New Records

**Important:** The system **always creates a new invoice record** (new UUID) when processing, even for duplicates:

```87:98:ingestion/orchestrator.py
    # Create invoice record
    invoice = Invoice(
        id=uuid.uuid4(),
        file_path=str(file_path.relative_to(data_dir)),
        file_name=file_path.name,
        file_hash=file_hash,
        file_size=file_size,
        file_type=file_type,
        version=version,
        processing_status=ProcessingStatus.PROCESSING,
        encrypted_file_path=encrypted_file_path,
    )
```

This means:
- ✅ **Complete history**: Every processing attempt is tracked separately
- ✅ **No data loss**: Previous processing results are preserved
- ✅ **Version tracking**: You can see all versions of the same file

## Example Scenario

Let's say you process `invoice-1.png` three times:

### First Processing
```
Invoice ID: abc-123
File Hash: 7a3f9b2c...
Version: 1
Status: completed
Created: 2024-12-19 10:00:00
```

### Second Processing (Same File)
```
Invoice ID: def-456  ← NEW UUID
File Hash: 7a3f9b2c...  ← SAME HASH
Version: 2  ← INCREMENTED
Status: completed
Created: 2024-12-19 11:00:00
```

### Third Processing (Same File)
```
Invoice ID: ghi-789  ← NEW UUID
File Hash: 7a3f9b2c...  ← SAME HASH
Version: 3  ← INCREMENTED
Status: completed
Created: 2024-12-19 12:00:00
```

**Result:** You'll have 3 separate invoice records, all with the same hash but different versions and timestamps.

## Force Reprocess Flag

The `force_reprocess` parameter controls version behavior:

```python
# Normal processing (increments version)
POST /api/v1/invoices/process
{
  "file_path": "invoice-1.png",
  "force_reprocess": false  # Default
}

# Force reprocess (starts at version 1)
POST /api/v1/invoices/process
{
  "file_path": "invoice-1.png",
  "force_reprocess": true
}
```

**With `force_reprocess=True`:**
- Always starts with `version = 1`
- Still creates a new invoice record
- Useful if you want to reset version numbering

## Database Schema

The `invoices` table tracks:
- `file_hash`: SHA-256 hash (indexed for fast lookup)
- `version`: Integer version number
- `id`: Unique UUID for each processing attempt

```72:75:core/models.py
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
```

## Querying by Hash

You can find all versions of the same file by querying the hash:

```sql
SELECT * FROM invoices 
WHERE file_hash = '7a3f9b2c...' 
ORDER BY version DESC;
```

## Important Notes

1. **Hash is content-based**: Two files with identical content will have the same hash, regardless of filename
2. **Version increments from latest**: The version is based on the **latest** existing invoice with that hash, not the total count
3. **No automatic deduplication**: The system doesn't prevent duplicate processing - it tracks it with versions
4. **Each processing is independent**: Each invoice record has its own extracted data and validation results

## Use Cases

- **Testing extraction improvements**: Reprocess same files to compare results
- **Re-validation**: Reprocess after updating validation rules
- **Audit trail**: Maintain complete history of all processing attempts
- **A/B testing**: Compare different extraction strategies on the same file

