"""SQLAlchemy models for invoice processing."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base
from core.configuration_models import (  # noqa: F401
    CapabilityContract,
    ConfigurationChangeEvent,
    FallbackPolicy,
    Module,
    ModuleConfiguration,
    ModuleSelection,
    ProcessingStage,
)


class ProcessingStatus(str, Enum):
    """Invoice processing status."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(str, Enum):
    """Validation result status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class JobType(str, Enum):
    """Processing job type."""

    FILE_INGESTION = "file_ingestion"
    OCR_PROCESSING = "ocr_processing"
    DATA_EXTRACTION = "data_extraction"
    VALIDATION = "validation"


class ExecutionType(str, Enum):
    """Job execution type."""

    ASYNC_COROUTINE = "async_coroutine"
    CPU_PROCESS = "cpu_process"


class Invoice(Base):
    """Invoice document model."""

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    group: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        String(20), nullable=False, default=ProcessingStatus.PENDING
    )
    encrypted_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Metadata columns (added in migration 925498b15ac8)
    file_preview_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    processing_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Multi-dataset Integration (added for HF datasets)
    source_dataset: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    annotation_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, default=1.0)
    image_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_training_data: Mapped[bool] = mapped_column(CheckConstraint("is_training_data IS NOT NULL"), default=False)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    extracted_data: Mapped["ExtractedData | None"] = relationship(
        "ExtractedData", back_populates="invoice", uselist=False
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        "ValidationResult", back_populates="invoice", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="invoice", cascade="all, delete-orphan"
    )
    line_item_details: Mapped[list["InvoiceLineItem"]] = relationship(
        "InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_invoices_status", "processing_status"),
        Index("idx_invoices_created_at", "created_at"),
        CheckConstraint(
            "file_hash ~ '^[a-f0-9]{64}$'", name="check_file_hash_format"
        ),
        CheckConstraint(
            "file_type IN ('pdf', 'xlsx', 'csv', 'xls', 'jpg', 'jpeg', 'png', 'webp', 'avif')",
            name="check_file_type",
        ),
        CheckConstraint("version >= 1", name="check_version_positive"),
    )


class ExtractedData(Base):
    """Extracted invoice data model."""

    __tablename__ = "extracted_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    vendor_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True, default="USD")
    line_items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Per-field confidence scores (added in migration 925498b15ac8)
    vendor_name_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    invoice_number_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    invoice_date_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    total_amount_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    subtotal_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    tax_amount_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    currency_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="extracted_data")

    # Indexes
    __table_args__ = (
        Index("idx_extracted_data_vendor", "vendor_name"),
        Index("idx_extracted_data_date", "invoice_date"),
        Index("idx_extracted_data_total_amount", "total_amount"),
        Index("idx_extracted_data_confidence", "extraction_confidence"),
        CheckConstraint("subtotal IS NULL OR subtotal::numeric >= 0", name="check_subtotal_non_negative"),
        CheckConstraint("tax_amount IS NULL OR tax_amount::numeric >= 0", name="check_tax_non_negative"),
        CheckConstraint("total_amount IS NULL OR total_amount::numeric >= 0", name="check_total_non_negative"),
        CheckConstraint(
            "tax_rate IS NULL OR (tax_rate::numeric >= 0 AND tax_rate::numeric <= 1)",
            name="check_tax_rate_range",
        ),
        CheckConstraint(
            "extraction_confidence IS NULL OR (extraction_confidence::numeric >= 0 AND extraction_confidence::numeric <= 1)",
            name="check_confidence_range",
        ),
    )


class ValidationResult(Base):
    """Validation result model."""

    __tablename__ = "validation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ValidationStatus] = mapped_column(String(20), nullable=False)
    expected_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tolerance: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="validation_results")

    # Indexes
    __table_args__ = (
        Index("idx_validation_results_invoice_id", "invoice_id"),
        Index("idx_validation_results_status", "status"),
        Index("idx_validation_results_rule", "rule_name"),
    )


class ProcessingJob(Base):
    """Processing job tracking model."""

    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_type: Mapped[JobType] = mapped_column(String(50), nullable=False)
    execution_type: Mapped[ExecutionType] = mapped_column(String(20), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        String(20), nullable=False, default=ProcessingStatus.PENDING
    )
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    job_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="processing_jobs")

    # Indexes
    __table_args__ = (
        Index("idx_processing_jobs_invoice_id", "invoice_id"),
        Index("idx_processing_jobs_status", "status"),
        Index("idx_processing_jobs_type", "job_type"),
        CheckConstraint("retry_count >= 0", name="check_retry_count_non_negative"),
    )


class OcrResult(Base):
    """OCR result record."""

    __tablename__ = "ocr_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    input_id: Mapped[str] = mapped_column(String(512), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_ocr_results_input", "input_id"),
        Index("idx_ocr_results_provider", "provider_id"),
        Index("idx_ocr_results_status", "status"),
    )


class OcrComparison(Base):
    """OCR comparison record."""

    __tablename__ = "ocr_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    input_id: Mapped[str] = mapped_column(String(512), nullable=False)
    provider_a_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ocr_results.id"), nullable=False
    )
    provider_b_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ocr_results.id"), nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_ocr_comparisons_input", "input_id"),
        Index("idx_ocr_comparisons_created", "created_at"),
    )

class InvoiceLineItem(Base):
    """Structured line item detail record."""

    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    line_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="line_item_details")


class DatasetSource(Base):
    """HuggingFace or other external dataset source registry."""

    __tablename__ = "dataset_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hf_repo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_synced: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class TrainingRun(Base):
    """ML training run tracking for model versioning."""

    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    datasets_used: Mapped[list[str]] = mapped_column(JSONB, nullable=False)  # Stored as list of strings
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
