# Quickstart: UI and Multi-Format Data Extraction Quality Improvements

**Feature**: UI and Multi-Format Data Extraction Quality  
**Date**: January 7, 2026  
**Branch**: `001-ui-data-extract-quality`

## Overview

This quickstart guide provides step-by-step instructions for implementing the UI and data extraction quality improvements. Follow the implementation phases in order, using Test-Driven Development (TDD) as mandated by the constitution.

## Prerequisites

Before starting implementation:

1. **Review Planning Documents**:
   - [spec.md](./spec.md) - Feature specification
   - [plan.md](./plan.md) - Implementation plan
   - [research.md](./research.md) - Technology decisions
   - [data-model.md](./data-model.md) - Schema changes
   - [contracts/](./contracts/) - API specifications

2. **Development Environment**:
   - Python 3.12 installed
   - PostgreSQL 17 running (via Docker Compose)
   - Virtual environment activated
   - Dependencies installed: `pip install -e ".[dev]"`

3. **Baseline Measurement**:
   ```bash
   # Measure current extraction accuracy before improvements
   python scripts/measure_accuracy.py --output baseline_metrics.json
   ```

## Implementation Phases

---

## Phase 1: Database Schema Migration (1-2 hours)

### Step 1.1: Create Migration File

Create a new Alembic migration:

```bash
alembic revision -m "add_per_field_confidence_tracking"
```

This creates a file like `alembic/versions/002_add_per_field_confidence.py`

### Step 1.2: Write Migration Script

Edit the generated migration file:

```python
"""Add per-field confidence tracking

Revision ID: 002
Revises: 001
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'  # Update to match your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add per-field confidence columns to extracted_data
    op.add_column('extracted_data', 
        sa.Column('vendor_name_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('invoice_number_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('invoice_date_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('total_amount_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('subtotal_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('tax_amount_confidence', sa.Numeric(3, 2), nullable=True))
    op.add_column('extracted_data', 
        sa.Column('currency_confidence', sa.Numeric(3, 2), nullable=True))
    
    # Add CHECK constraints for confidence range
    op.create_check_constraint(
        'check_vendor_conf_range',
        'extracted_data',
        'vendor_name_confidence IS NULL OR (vendor_name_confidence >= 0 AND vendor_name_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_invoice_num_conf_range',
        'extracted_data',
        'invoice_number_confidence IS NULL OR (invoice_number_confidence >= 0 AND invoice_number_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_invoice_date_conf_range',
        'extracted_data',
        'invoice_date_confidence IS NULL OR (invoice_date_confidence >= 0 AND invoice_date_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_total_conf_range',
        'extracted_data',
        'total_amount_confidence IS NULL OR (total_amount_confidence >= 0 AND total_amount_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_subtotal_conf_range',
        'extracted_data',
        'subtotal_confidence IS NULL OR (subtotal_confidence >= 0 AND subtotal_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_tax_conf_range',
        'extracted_data',
        'tax_amount_confidence IS NULL OR (tax_amount_confidence >= 0 AND tax_amount_confidence <= 1)'
    )
    op.create_check_constraint(
        'check_currency_conf_range',
        'extracted_data',
        'currency_confidence IS NULL OR (currency_confidence >= 0 AND currency_confidence <= 1)'
    )
    
    # Add indexes for filtering and sorting
    op.create_index('idx_extracted_data_vendor_conf', 'extracted_data', ['vendor_name_confidence'])
    op.create_index('idx_extracted_data_invoice_num_conf', 'extracted_data', ['invoice_number_confidence'])
    op.create_index('idx_extracted_data_total_conf', 'extracted_data', ['total_amount_confidence'])
    
    # Add expression index for low-confidence filtering
    op.execute("""
        CREATE INDEX idx_extracted_data_low_confidence ON extracted_data(
            (COALESCE(vendor_name_confidence, 0) + COALESCE(invoice_number_confidence, 0) + COALESCE(total_amount_confidence, 0))
        )
    """)
    
    # Add metadata columns to invoices
    op.add_column('invoices', sa.Column('file_preview_metadata', postgresql.JSONB(), nullable=True))
    op.add_column('invoices', sa.Column('processing_metadata', postgresql.JSONB(), nullable=True))
    
    # Add index for batch ID lookup
    op.execute("""
        CREATE INDEX idx_invoices_batch_id ON invoices((processing_metadata->>'parallel_batch_id'))
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_invoices_batch_id', 'invoices')
    op.drop_index('idx_extracted_data_low_confidence', 'extracted_data')
    op.drop_index('idx_extracted_data_total_conf', 'extracted_data')
    op.drop_index('idx_extracted_data_invoice_num_conf', 'extracted_data')
    op.drop_index('idx_extracted_data_vendor_conf', 'extracted_data')
    
    # Drop constraints
    op.drop_constraint('check_currency_conf_range', 'extracted_data')
    op.drop_constraint('check_tax_conf_range', 'extracted_data')
    op.drop_constraint('check_subtotal_conf_range', 'extracted_data')
    op.drop_constraint('check_total_conf_range', 'extracted_data')
    op.drop_constraint('check_invoice_date_conf_range', 'extracted_data')
    op.drop_constraint('check_invoice_num_conf_range', 'extracted_data')
    op.drop_constraint('check_vendor_conf_range', 'extracted_data')
    
    # Drop columns from invoices
    op.drop_column('invoices', 'processing_metadata')
    op.drop_column('invoices', 'file_preview_metadata')
    
    # Drop columns from extracted_data
    op.drop_column('extracted_data', 'currency_confidence')
    op.drop_column('extracted_data', 'tax_amount_confidence')
    op.drop_column('extracted_data', 'subtotal_confidence')
    op.drop_column('extracted_data', 'total_amount_confidence')
    op.drop_column('extracted_data', 'invoice_date_confidence')
    op.drop_column('extracted_data', 'invoice_number_confidence')
    op.drop_column('extracted_data', 'vendor_name_confidence')
```

### Step 1.3: Run Migration

```bash
# Run migration
alembic upgrade head

# Verify migration
alembic current
```

### Step 1.4: Update SQLAlchemy Models

Edit `core/models.py`:

```python
# Add to ExtractedData class
class ExtractedData(Base):
    __tablename__ = "extracted_data"
    
    # ... existing columns ...
    
    # NEW: Per-field confidence scores
    vendor_name_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    invoice_number_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    invoice_date_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    total_amount_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    subtotal_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    tax_amount_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    currency_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

# Add to Invoice class
class Invoice(Base):
    __tablename__ = "invoices"
    
    # ... existing columns ...
    
    # NEW: Metadata columns
    file_preview_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    processing_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

### Step 1.5: Update Pydantic Schemas

Edit `brain/schemas.py`:

```python
class ExtractedDataSchema(BaseModel):
    # ... existing fields ...
    
    # NEW: Per-field confidence scores
    vendor_name_confidence: Decimal | None = Field(None, ge=0, le=1, description="Vendor name confidence")
    invoice_number_confidence: Decimal | None = Field(None, ge=0, le=1, description="Invoice number confidence")
    invoice_date_confidence: Decimal | None = Field(None, ge=0, le=1, description="Invoice date confidence")
    total_amount_confidence: Decimal | None = Field(None, ge=0, le=1, description="Total amount confidence")
    subtotal_confidence: Decimal | None = Field(None, ge=0, le=1, description="Subtotal confidence")
    tax_amount_confidence: Decimal | None = Field(None, ge=0, le=1, description="Tax amount confidence")
    currency_confidence: Decimal | None = Field(None, ge=0, le=1, description="Currency confidence")
    
    @model_validator(mode='after')
    def calculate_overall_confidence(self) -> 'ExtractedDataSchema':
        """Calculate overall extraction confidence from per-field scores."""
        if self.extraction_confidence is None:
            confidences = [
                self.vendor_name_confidence,
                self.invoice_number_confidence,
                self.total_amount_confidence,
            ]
            non_null_confidences = [c for c in confidences if c is not None]
            if non_null_confidences:
                self.extraction_confidence = Decimal(sum(non_null_confidences)) / Decimal(len(non_null_confidences))
        return self
```

---

## Phase 2: Enhanced Extraction Logic (4-6 hours)

### Step 2.1: Write Tests First (TDD)

Create `tests/unit/test_format_specific_extraction.py`:

```python
"""Tests for format-specific extraction enhancements."""

import pytest
from decimal import Decimal
from brain.extractor import extract_invoice_data
from brain.schemas import ExtractedDataSchema


@pytest.mark.asyncio
async def test_excel_column_header_extraction():
    """Test that Excel data with column headers is extracted correctly."""
    # Simulate Excel-processed text with clear column headers
    raw_text = """
    Sheet: Invoices
    
         Vendor  | Invoice # | Date       | Amount
    --------------------------------------------------
    ACME Corp   | INV-001   | 2024-01-15 | 1100.00
    """
    
    metadata = {
        "file_type": "xlsx",
        "file_name": "invoices.xlsx",
        "excel_columns": ["Vendor", "Invoice #", "Date", "Amount"],
    }
    
    result = await extract_invoice_data(raw_text, metadata=metadata)
    
    assert result.vendor_name == "ACME Corp"
    assert result.invoice_number == "INV-001"
    assert result.total_amount == Decimal("1100.00")
    assert result.vendor_name_confidence is not None
    assert result.vendor_name_confidence > Decimal("0.85")  # High confidence for structured data


@pytest.mark.asyncio
async def test_pdf_text_extraction_confidence():
    """Test that PDF with embedded text has high confidence."""
    raw_text = "Invoice from ACME Corporation, Invoice #: INV-2024-001, Total: $1,100.00"
    
    metadata = {
        "file_type": "pdf",
        "has_text_layer": True,
        "extraction_method": "text",
    }
    
    result = await extract_invoice_data(raw_text, metadata=metadata)
    
    assert result.vendor_name == "ACME Corporation"
    assert result.vendor_name_confidence > Decimal("0.80")  # Higher confidence for text PDFs


@pytest.mark.asyncio
async def test_image_ocr_confidence_propagation():
    """Test that OCR confidence scores are propagated to fields."""
    raw_text = "ACME Corp\nInvoice: INV-001\nTotal: $500.00"
    
    metadata = {
        "file_type": "jpg",
        "extraction_method": "ocr",
        "ocr_confidences": {
            "ACME Corp": 0.92,
            "INV-001": 0.88,
            "$500.00": 0.95,
        },
    }
    
    result = await extract_invoice_data(raw_text, metadata=metadata)
    
    # Confidence should reflect OCR scores
    assert result.vendor_name_confidence is not None
    assert Decimal("0.85") <= result.vendor_name_confidence <= Decimal("0.95")


@pytest.mark.asyncio
async def test_null_field_has_zero_confidence():
    """Test that NULL fields have 0.0 confidence."""
    raw_text = "Some text with no invoice data"
    
    result = await extract_invoice_data(raw_text, metadata={})
    
    if result.vendor_name is None:
        assert result.vendor_name_confidence == Decimal("0.0") or result.vendor_name_confidence is None
```

### Step 2.2: Enhance Extraction Function

Edit `brain/extractor.py` to add format-specific extraction:

```python
async def extract_invoice_data(raw_text: str, metadata: dict[str, Any] | None = None) -> ExtractedDataSchema:
    """Extract structured invoice data with format-specific strategies."""
    
    logger.info("Extracting invoice data", text_length=len(raw_text), metadata=metadata)
    
    if not raw_text.strip():
        return ExtractedDataSchema(raw_text=raw_text, extraction_confidence=Decimal("0.0"))
    
    # Detect file type and apply format-specific preprocessing
    file_type = metadata.get("file_type") if metadata else None
    format_hints = _generate_format_hints(file_type, metadata)
    
    # Build enhanced system prompt with format-specific guidance
    system_prompt = _build_extraction_prompt(format_hints)
    
    # ... existing LLM extraction logic ...
    
    # Calculate per-field confidence scores
    extracted = ExtractedDataSchema(**data)
    extracted = _calculate_field_confidences(extracted, metadata, validation_passed=True)
    
    return extracted


def _generate_format_hints(file_type: str | None, metadata: dict | None) -> str:
    """Generate format-specific hints for LLM extraction."""
    
    if not file_type or not metadata:
        return ""
    
    hints = []
    
    if file_type in {"xlsx", "csv"}:
        # Excel/CSV specific hints
        if "excel_columns" in metadata:
            column_list = ", ".join(metadata["excel_columns"])
            hints.append(f"DATA FORMAT: Structured spreadsheet with columns: {column_list}")
            hints.append("EXTRACTION STRATEGY: Map column headers to invoice fields. Use exact column positions.")
        
        if metadata.get("has_headers"):
            hints.append("First row contains column headers. Use these to identify fields.")
    
    elif file_type == "pdf":
        # PDF specific hints
        if metadata.get("has_text_layer"):
            hints.append("DATA FORMAT: PDF with embedded text (not scanned). Extraction should be highly accurate.")
        else:
            hints.append("DATA FORMAT: Scanned PDF (image-based). OCR text may contain errors. Use context to correct.")
        
        if metadata.get("page_count", 1) > 1:
            hints.append(f"Multi-page document ({metadata['page_count']} pages). Invoice data may span pages.")
    
    elif file_type in {"jpg", "png", "webp", "avif"}:
        # Image specific hints
        hints.append("DATA FORMAT: Scanned invoice image. OCR text may have errors (e.g., 'O' vs '0', 'I' vs '1').")
        
        if "ocr_confidences" in metadata:
            hints.append("OCR confidence scores available. Low-confidence words may need correction.")
    
    return "\n".join(hints)


def _calculate_field_confidences(
    extracted: ExtractedDataSchema,
    metadata: dict | None,
    validation_passed: bool = True
) -> ExtractedDataSchema:
    """Calculate per-field confidence scores."""
    
    # Strategy 1: Use OCR confidence if available
    if metadata and "ocr_confidences" in metadata:
        ocr_confs = metadata["ocr_confidences"]
        
        # Map OCR confidences to fields (simplified - real implementation would be more sophisticated)
        if extracted.vendor_name:
            extracted.vendor_name_confidence = Decimal(str(ocr_confs.get(extracted.vendor_name, 0.85)))
        
        if extracted.invoice_number:
            extracted.invoice_number_confidence = Decimal(str(ocr_confs.get(extracted.invoice_number, 0.85)))
    
    # Strategy 2: Use validation-based confidence
    else:
        base_confidence = Decimal("0.95") if validation_passed else Decimal("0.60")
        
        extracted.vendor_name_confidence = base_confidence if extracted.vendor_name else Decimal("0.0")
        extracted.invoice_number_confidence = base_confidence if extracted.invoice_number else Decimal("0.0")
        extracted.invoice_date_confidence = base_confidence if extracted.invoice_date else Decimal("0.0")
        extracted.total_amount_confidence = base_confidence if extracted.total_amount else Decimal("0.0")
        extracted.subtotal_confidence = base_confidence if extracted.subtotal else Decimal("0.0")
        extracted.tax_amount_confidence = base_confidence if extracted.tax_amount else Decimal("0.0")
        extracted.currency_confidence = base_confidence if extracted.currency else Decimal("0.0")
    
    # Strategy 3: Boost confidence for structured formats
    if metadata and metadata.get("file_type") in {"xlsx", "csv"} and metadata.get("has_headers"):
        # Excel with headers = high confidence
        confidence_boost = Decimal("0.05")
        if extracted.vendor_name_confidence:
            extracted.vendor_name_confidence = min(Decimal("1.0"), extracted.vendor_name_confidence + confidence_boost)
        if extracted.invoice_number_confidence:
            extracted.invoice_number_confidence = min(Decimal("1.0"), extracted.invoice_number_confidence + confidence_boost)
    
    return extracted
```

### Step 2.3: Run Tests

```bash
pytest tests/unit/test_format_specific_extraction.py -v
```

Fix implementation until all tests pass.

---

## Phase 3: File Preview Components (3-4 hours)

### Step 3.1: Create Preview Utility Module

Create `ingestion/file_preview.py`:

```python
"""File preview utilities for dashboard display."""

import base64
from pathlib import Path
from typing import Any
import pandas as pd
from core.logging import get_logger

logger = get_logger(__name__)

MAX_PREVIEW_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


async def generate_preview_data(file_path: Path, file_type: str) -> dict[str, Any]:
    """Generate preview data for file display.
    
    Args:
        file_path: Path to the file
        file_type: File type (pdf, csv, xlsx, jpg, etc.)
    
    Returns:
        Dictionary with preview data and metadata
    """
    
    file_size = file_path.stat().st_size
    
    if file_size > MAX_PREVIEW_SIZE_BYTES:
        raise ValueError(f"File size {file_size} exceeds preview limit of {MAX_PREVIEW_SIZE_BYTES} bytes")
    
    if file_type == "pdf":
        return await _preview_pdf(file_path)
    elif file_type in {"csv"}:
        return await _preview_csv(file_path)
    elif file_type in {"xlsx", "xls"}:
        return await _preview_excel(file_path)
    elif file_type in {"jpg", "png", "webp", "avif"}:
        return await _preview_image(file_path)
    else:
        raise ValueError(f"Unsupported file type for preview: {file_type}")


async def _preview_pdf(file_path: Path) -> dict[str, Any]:
    """Generate PDF preview as base64-encoded content."""
    
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    
    base64_content = base64.b64encode(pdf_bytes).decode("utf-8")
    
    # Try to get page count (requires pypdf)
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        page_count = len(reader.pages)
        has_text = bool(reader.pages[0].extract_text().strip()) if page_count > 0 else False
    except Exception as e:
        logger.warning("Failed to extract PDF metadata", error=str(e))
        page_count = None
        has_text = None
    
    return {
        "format": "base64_pdf",
        "content": base64_content,
        "mime_type": "application/pdf",
        "metadata": {
            "page_count": page_count,
            "has_text_layer": has_text,
        },
    }


async def _preview_csv(file_path: Path, max_rows: int = 100) -> dict[str, Any]:
    """Generate CSV preview as tabular data."""
    
    df = pd.read_csv(file_path, nrows=max_rows)
    total_rows = sum(1 for _ in open(file_path)) - 1  # Count total rows (minus header)
    
    return {
        "format": "tabular",
        "columns": df.columns.tolist(),
        "rows": df.values.tolist(),
        "total_rows": total_rows,
        "displayed_rows": len(df),
        "metadata": {
            "has_headers": True,
            "column_count": len(df.columns),
        },
    }


async def _preview_excel(file_path: Path, max_rows: int = 100) -> dict[str, Any]:
    """Generate Excel preview as tabular data."""
    
    # Read first sheet only
    df = pd.read_excel(file_path, nrows=max_rows)
    
    # Get total row count from Excel file
    excel_file = pd.ExcelFile(file_path)
    full_df = excel_file.parse(excel_file.sheet_names[0])
    total_rows = len(full_df)
    
    return {
        "format": "tabular",
        "columns": df.columns.tolist(),
        "rows": df.values.tolist(),
        "total_rows": total_rows,
        "displayed_rows": len(df),
        "metadata": {
            "has_headers": True,
            "column_count": len(df.columns),
            "sheet_count": len(excel_file.sheet_names),
            "sheet_name": excel_file.sheet_names[0],
        },
    }


async def _preview_image(file_path: Path) -> dict[str, Any]:
    """Generate image preview as base64-encoded content."""
    
    with open(file_path, "rb") as f:
        image_bytes = f.read()
    
    base64_content = base64.b64encode(image_bytes).decode("utf-8")
    
    # Get image metadata (requires Pillow)
    try:
        from PIL import Image
        img = Image.open(file_path)
        width, height = img.size
        format_name = img.format
        dpi = img.info.get("dpi", (72, 72))[0]
    except Exception as e:
        logger.warning("Failed to extract image metadata", error=str(e))
        width, height, format_name, dpi = None, None, None, None
    
    # Determine MIME type
    ext = file_path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".avif": "image/avif",
    }
    mime_type = mime_types.get(ext, "image/jpeg")
    
    return {
        "format": "base64_image",
        "content": base64_content,
        "mime_type": mime_type,
        "metadata": {
            "width": width,
            "height": height,
            "format": format_name,
            "dpi": dpi,
        },
    }
```

### Step 3.2: Add API Endpoint

Edit `interface/api/routes/invoices.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from ingestion.file_preview import generate_preview_data
from core.config import settings

router = APIRouter()

@router.get("/invoices/{invoice_id}/preview")
async def get_invoice_preview(
    invoice_id: str,
    session: AsyncSession = Depends(get_db_session),
    preview_type: str = Query("auto", enum=["auto", "thumbnail", "full", "data_only"]),
    max_rows: int = Query(100, ge=10, le=1000),
):
    """Get file preview for an invoice."""
    
    # Fetch invoice
    result = await session.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Build file path
    file_path = Path(settings.DATA_DIR) / invoice.storage_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Invoice file not found on disk")
    
    # Check cache
    cached_preview = invoice.file_preview_metadata
    if cached_preview and preview_type == "full":
        # Serve from cache if available and matches requested type
        return {
            "status": "success",
            "data": {
                "invoice_id": str(invoice.id),
                "file_name": invoice.file_name,
                "file_type": invoice.file_type,
                "preview_data": cached_preview,
                "cached": True,
            },
        }
    
    # Generate preview
    try:
        preview_data = await generate_preview_data(file_path, invoice.file_type)
        
        # Cache preview data
        invoice.file_preview_metadata = preview_data
        await session.commit()
        
        return {
            "status": "success",
            "data": {
                "invoice_id": str(invoice.id),
                "file_name": invoice.file_name,
                "file_type": invoice.file_type,
                "file_size_bytes": file_path.stat().st_size,
                "preview_type": preview_type,
                "preview_data": preview_data,
                "cached": False,
            },
        }
    
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.error("Failed to generate preview", invoice_id=invoice_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate preview")
```

### Step 3.3: Create Streamlit Preview Components

Create `interface/dashboard/components/file_preview.py`:

```python
"""File preview components for Streamlit dashboard."""

import streamlit as st
import pandas as pd
import base64
from pathlib import Path


def render_file_preview(invoice: dict):
    """Render file preview based on file type."""
    
    file_type = invoice.get("file_type")
    file_path = Path(invoice.get("storage_path", ""))
    
    if not file_path.exists():
        st.error("❌ File not found on disk")
        return
    
    st.subheader(f"📄 File Preview: {invoice.get('file_name', 'Unknown')}")
    
    try:
        if file_type == "pdf":
            _render_pdf_preview(file_path)
        elif file_type in {"csv"}:
            _render_csv_preview(file_path)
        elif file_type in {"xlsx", "xls"}:
            _render_excel_preview(file_path)
        elif file_type in {"jpg", "png", "webp", "avif"}:
            _render_image_preview(file_path)
        else:
            st.warning(f"⚠️ Preview not available for file type: {file_type}")
    
    except Exception as e:
        st.error(f"❌ Failed to load preview: {e}")


def _render_pdf_preview(file_path: Path):
    """Render PDF preview using base64 encoding."""
    
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    
    # Embed PDF in iframe
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def _render_csv_preview(file_path: Path, max_rows: int = 100):
    """Render CSV preview as dataframe."""
    
    df = pd.read_csv(file_path, nrows=max_rows)
    
    st.info(f"ℹ️ Showing first {len(df)} rows (file may contain more)")
    st.dataframe(df, use_container_width=True, height=400)


def _render_excel_preview(file_path: Path, max_rows: int = 100):
    """Render Excel preview as dataframe."""
    
    df = pd.read_excel(file_path, nrows=max_rows)
    
    st.info(f"ℹ️ Showing first {len(df)} rows of the first sheet")
    st.dataframe(df, use_container_width=True, height=400)


def _render_image_preview(file_path: Path):
    """Render image preview."""
    
    st.image(str(file_path), use_container_width=True)
```

### Step 3.4: Integrate Preview into Invoice Detail View

Edit `interface/dashboard/app.py`:

```python
from interface.dashboard.components.file_preview import render_file_preview

def display_invoice_detail(invoice_id: str | None):
    """Display detailed invoice information with file preview."""
    
    # ... existing code to fetch invoice ...
    
    # Add preview tab
    detail_tabs = st.tabs(["📊 Extracted Data", "📄 File Preview", "✅ Validation Results", "📝 Raw Text"])
    
    with detail_tabs[0]:
        # ... existing extracted data display ...
        pass
    
    with detail_tabs[1]:
        # NEW: File preview
        render_file_preview(invoice)
    
    with detail_tabs[2]:
        # ... existing validation display ...
        pass
    
    with detail_tabs[3]:
        # ... existing raw text display ...
        pass
```

---

## Phase 4: Parallel Processing (2-3 hours)

### Step 4.1: Add Batch Processing Function

Edit `ingestion/orchestrator.py`:

```python
import asyncio
from typing import List
import uuid

async def process_invoice_batch(
    file_paths: List[Path],
    data_dir: Path,
    session_factory,  # Use session factory, not a single session
    max_concurrency: int = 20,
    **kwargs
) -> List[Invoice]:
    """Process multiple invoices in parallel with concurrency limit.
    
    Args:
        file_paths: List of file paths to process
        data_dir: Data directory root
        session_factory: Async session factory for creating sessions per task
        max_concurrency: Maximum concurrent processing operations
        **kwargs: Additional arguments passed to process_invoice_file
    
    Returns:
        List of processed Invoice objects
    """
    
    batch_id = f"batch-{datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    logger.info("Starting batch processing", batch_id=batch_id, file_count=len(file_paths), max_concurrency=max_concurrency)
    
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_with_limit(file_path: Path, slot: int) -> Invoice:
        """Process single file with semaphore limiting."""
        async with semaphore:
            # Create new session for this task
            async with session_factory() as session:
                logger.info("Processing invoice in slot", file_path=str(file_path), slot=slot, batch_id=batch_id)
                
                # Add batch metadata
                processing_metadata = kwargs.get("processing_metadata", {})
                processing_metadata.update({
                    "parallel_batch_id": batch_id,
                    "concurrent_slot": slot,
                })
                
                try:
                    invoice = await process_invoice_file(
                        file_path=file_path,
                        data_dir=data_dir,
                        session=session,
                        **{**kwargs, "processing_metadata": processing_metadata}
                    )
                    await session.commit()
                    return invoice
                except Exception as e:
                    await session.rollback()
                    logger.error("Batch processing failed for invoice", file_path=str(file_path), error=str(e), batch_id=batch_id)
                    raise
    
    # Create tasks with slot numbers
    tasks = [process_with_limit(fp, idx) for idx, fp in enumerate(file_paths)]
    
    # Execute with progress tracking
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Separate successful and failed
    successful = [r for r in results if isinstance(r, Invoice)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    logger.info(
        "Batch processing completed",
        batch_id=batch_id,
        total=len(file_paths),
        successful=len(successful),
        failed=len(failed),
    )
    
    return successful
```

### Step 4.2: Update Processing Script

Edit `scripts/process_invoices.py` to support batch mode:

```python
# Add batch processing option
parser.add_argument("--batch", action="store_true", help="Process all files in parallel")
parser.add_argument("--max-concurrency", type=int, default=20, help="Max concurrent processing")

if args.batch:
    # Collect all files first
    files = []
    async for file_path in discover_files(data_dir):
        files.append(file_path)
    
    logger.info(f"Found {len(files)} files for batch processing")
    
    # Process in parallel
    results = await process_invoice_batch(
        file_paths=files,
        data_dir=data_dir,
        session_factory=get_session_factory(),
        max_concurrency=args.max_concurrency,
    )
    
    logger.info(f"Batch processing completed: {len(results)} successful")
```

---

## Phase 5: Quality Metrics Dashboard (2-3 hours)

### Step 5.1: Create Quality Metrics Queries

Create `interface/dashboard/queries/quality_metrics.py`:

```python
"""Quality metrics database queries."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Invoice, ExtractedData


async def get_quality_summary(session: AsyncSession) -> dict:
    """Get overall quality metrics summary."""
    
    # Total invoices
    total_result = await session.execute(
        select(func.count(Invoice.id)).where(Invoice.processing_status == "completed")
    )
    total_invoices = total_result.scalar()
    
    # Critical fields completeness
    completeness_result = await session.execute(
        select(
            func.count(ExtractedData.invoice_id).label("total"),
            func.count(ExtractedData.vendor_name).label("vendor_present"),
            func.count(ExtractedData.invoice_number).label("invoice_num_present"),
            func.count(ExtractedData.total_amount).label("total_amount_present"),
        )
    )
    completeness = completeness_result.one()
    
    # Average confidence scores
    confidence_result = await session.execute(
        select(
            func.avg(ExtractedData.vendor_name_confidence).label("avg_vendor_conf"),
            func.avg(ExtractedData.invoice_number_confidence).label("avg_invoice_num_conf"),
            func.avg(ExtractedData.total_amount_confidence).label("avg_total_conf"),
        )
    )
    confidences = confidence_result.one()
    
    return {
        "total_invoices": total_invoices,
        "critical_fields_complete": {
            "vendor_name": completeness.vendor_present,
            "invoice_number": completeness.invoice_num_present,
            "total_amount": completeness.total_amount_present,
        },
        "avg_confidence": {
            "vendor_name": float(confidences.avg_vendor_conf or 0),
            "invoice_number": float(confidences.avg_invoice_num_conf or 0),
            "total_amount": float(confidences.avg_total_conf or 0),
        },
    }


async def get_quality_by_format(session: AsyncSession) -> list[dict]:
    """Get quality metrics grouped by file format."""
    
    result = await session.execute(
        select(
            Invoice.file_type,
            func.count(Invoice.id).label("total"),
            func.count(ExtractedData.vendor_name).label("vendor_extracted"),
            func.avg(ExtractedData.vendor_name_confidence).label("avg_vendor_conf"),
            func.avg(ExtractedData.invoice_number_confidence).label("avg_invoice_num_conf"),
            func.avg(ExtractedData.total_amount_confidence).label("avg_total_conf"),
        )
        .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
        .where(Invoice.processing_status == "completed")
        .group_by(Invoice.file_type)
    )
    
    return [
        {
            "file_type": row.file_type,
            "total": row.total,
            "vendor_extracted": row.vendor_extracted,
            "avg_vendor_conf": float(row.avg_vendor_conf or 0),
            "avg_invoice_num_conf": float(row.avg_invoice_num_conf or 0),
            "avg_total_conf": float(row.avg_total_conf or 0),
        }
        for row in result
    ]
```

### Step 5.2: Create Quality Metrics Component

Create `interface/dashboard/components/quality_metrics.py`:

```python
"""Quality metrics dashboard component."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from interface.dashboard.queries.quality_metrics import get_quality_summary, get_quality_by_format


def render_quality_dashboard():
    """Render quality metrics dashboard."""
    
    st.header("📊 Data Extraction Quality Metrics")
    
    # Fetch data
    summary = asyncio.run(get_quality_summary(get_db_session()))
    by_format = asyncio.run(get_quality_by_format(get_db_session()))
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invoices", summary["total_invoices"])
    
    with col2:
        vendor_pct = (summary["critical_fields_complete"]["vendor_name"] / summary["total_invoices"]) * 100
        st.metric("Vendor Extracted", f"{vendor_pct:.1f}%")
    
    with col3:
        invoice_num_pct = (summary["critical_fields_complete"]["invoice_number"] / summary["total_invoices"]) * 100
        st.metric("Invoice # Extracted", f"{invoice_num_pct:.1f}%")
    
    with col4:
        total_pct = (summary["critical_fields_complete"]["total_amount"] / summary["total_invoices"]) * 100
        st.metric("Total Amount Extracted", f"{total_pct:.1f}%")
    
    st.divider()
    
    # Confidence by format chart
    st.subheader("Average Confidence by File Format")
    
    if by_format:
        df_format = pd.DataFrame(by_format)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_format["file_type"],
            y=df_format["avg_vendor_conf"],
            name="Vendor Name",
        ))
        fig.add_trace(go.Bar(
            x=df_format["file_type"],
            y=df_format["avg_invoice_num_conf"],
            name="Invoice Number",
        ))
        fig.add_trace(go.Bar(
            x=df_format["file_type"],
            y=df_format["avg_total_conf"],
            name="Total Amount",
        ))
        
        fig.update_layout(
            barmode="group",
            yaxis_title="Confidence Score",
            xaxis_title="File Format",
            yaxis_range=[0, 1.0],
        )
        
        st.plotly_chart(fig, use_container_width=True)
```

---

## Testing Strategy

### Unit Tests
```bash
# Run unit tests for extraction logic
pytest tests/unit/test_extraction_strategies.py -v

# Run unit tests for file preview
pytest tests/unit/test_file_preview.py -v

# Run unit tests for parallel processing
pytest tests/unit/test_parallel_processing.py -v
```

### Integration Tests
```bash
# Test end-to-end preview workflow
pytest tests/integration/test_preview_workflow.py -v

# Test quality API endpoints
pytest tests/integration/test_quality_api.py -v
```

### Manual Testing Checklist

1. **File Preview**:
   - [ ] Upload PDF, open invoice detail, verify preview renders
   - [ ] Upload CSV, verify tabular preview with correct column headers
   - [ ] Upload Excel, verify data displays correctly
   - [ ] Upload image, verify image displays

2. **Extraction Quality**:
   - [ ] Process 10 Excel invoices, verify >90% accuracy
   - [ ] Check confidence scores are populated
   - [ ] Verify low-confidence invoices are highlighted

3. **Parallel Processing**:
   - [ ] Upload 20 invoices, verify all process successfully
   - [ ] Check processing time is <30s for batch of 20
   - [ ] Verify database connection pool handles load

4. **Quality Dashboard**:
   - [ ] Open quality metrics tab
   - [ ] Verify charts render with correct data
   - [ ] Test filters (confidence range, file type)

---

## Performance Validation

After implementation, validate performance targets:

```bash
# Measure extraction accuracy improvement
python scripts/measure_accuracy.py --output after_metrics.json

# Compare baseline vs. after
python scripts/compare_metrics.py baseline_metrics.json after_metrics.json

# Test parallel processing performance
python scripts/benchmark_parallel.py --files 20 --concurrency 10

# Test dashboard load time
python scripts/benchmark_dashboard.py --invoice-count 1000
```

**Success Criteria**:
- Extraction accuracy: ≥85% for critical fields
- Excel accuracy: ≥95%
- File preview load: <2s for <10MB files
- Dashboard load: <3s for 1000 invoices
- Parallel processing: 20 invoices in <20s

---

## Deployment Checklist

Before merging to main:

- [ ] All tests passing
- [ ] Test coverage ≥80% for core modules
- [ ] Manual testing completed
- [ ] Performance benchmarks meet targets
- [ ] Database migration tested on staging
- [ ] API documentation updated
- [ ] User guide created
- [ ] Code review approved
- [ ] No linter errors (ruff, mypy pass)

---

## Troubleshooting

### Issue: PDF Preview Not Rendering
**Solution**: Check file size < 10MB, verify base64 encoding is correct, try different PDF

### Issue: Low Extraction Confidence
**Solution**: Check LLM prompt includes format hints, verify metadata is passed correctly

### Issue: Parallel Processing Fails
**Solution**: Check database connection pool size, verify semaphore limit is set, check memory usage

### Issue: Dashboard Slow
**Solution**: Verify indexes exist on confidence columns, check query execution plans, add caching

---

## Next Steps

After completing this implementation:

1. Generate detailed task breakdown: `/speckit.tasks`
2. Monitor extraction accuracy in production
3. Collect user feedback on UI improvements
4. Iterate on extraction prompts based on failure analysis
5. Consider additional format-specific optimizations (e.g., table detection for PDFs)

---

**Questions or Issues?**
- Check [research.md](./research.md) for technology decisions
- Review [data-model.md](./data-model.md) for schema details
- Consult [contracts/](./contracts/) for API specifications
- Refer to constitution for quality standards

