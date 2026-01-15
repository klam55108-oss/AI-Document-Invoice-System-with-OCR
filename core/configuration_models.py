"""Database models for resilient configuration."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class ModuleStatus(str, Enum):
    """Module availability status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"


class ConfigurationStatus(str, Enum):
    """Configuration lifecycle status."""

    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class CapabilityContract(Base):
    """Capability contract definition for a processing stage."""

    __tablename__ = "capability_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    inputs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    outputs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    guarantees: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    stages: Mapped[list["ProcessingStage"]] = relationship(
        "ProcessingStage", back_populates="capability_contract"
    )
    modules: Mapped[list["Module"]] = relationship("Module", back_populates="capability_contract")


class ProcessingStage(Base):
    """Discrete step in the invoice workflow."""

    __tablename__ = "processing_stages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    capability_contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capability_contracts.id"), nullable=False
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    capability_contract: Mapped[CapabilityContract] = relationship(
        "CapabilityContract", back_populates="stages"
    )
    modules: Mapped[list["Module"]] = relationship("Module", back_populates="stage")
    selections: Mapped[list["ModuleSelection"]] = relationship(
        "ModuleSelection", back_populates="stage"
    )
    fallback_policies: Mapped[list["FallbackPolicy"]] = relationship(
        "FallbackPolicy", back_populates="stage"
    )


class Module(Base):
    """Pluggable module implementation."""

    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processing_stages.id"), nullable=False
    )
    capability_contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("capability_contracts.id"), nullable=False
    )
    status: Mapped[ModuleStatus] = mapped_column(
        String(20), nullable=False, default=ModuleStatus.AVAILABLE
    )
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    stage: Mapped[ProcessingStage] = relationship("ProcessingStage", back_populates="modules")
    capability_contract: Mapped[CapabilityContract] = relationship(
        "CapabilityContract", back_populates="modules"
    )
    selections: Mapped[list["ModuleSelection"]] = relationship(
        "ModuleSelection", back_populates="module"
    )

    __table_args__ = (
        Index("idx_modules_stage", "stage_id"),
        Index("idx_modules_status", "status"),
    )


class ModuleConfiguration(Base):
    """Versioned module configuration."""

    __tablename__ = "module_configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ConfigurationStatus] = mapped_column(
        String(20), nullable=False, default=ConfigurationStatus.DRAFT
    )
    created_by: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    selections: Mapped[list["ModuleSelection"]] = relationship(
        "ModuleSelection", back_populates="configuration", cascade="all, delete-orphan"
    )
    events: Mapped[list["ConfigurationChangeEvent"]] = relationship(
        "ConfigurationChangeEvent", back_populates="configuration", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_module_config_status", "status"),)


class ModuleSelection(Base):
    """Stage-to-module selection within a configuration."""

    __tablename__ = "module_selections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("module_configurations.id"), nullable=False
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processing_stages.id"), nullable=False
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    configuration: Mapped[ModuleConfiguration] = relationship(
        "ModuleConfiguration", back_populates="selections"
    )
    stage: Mapped[ProcessingStage] = relationship("ProcessingStage", back_populates="selections")
    module: Mapped[Module] = relationship("Module", back_populates="selections")

    __table_args__ = (Index("idx_module_selection_stage", "stage_id"),)


class FallbackPolicy(Base):
    """Fallback behavior for a processing stage."""

    __tablename__ = "fallback_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processing_stages.id"), nullable=False
    )
    fallback_module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False
    )
    trigger_conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    stage: Mapped[ProcessingStage] = relationship("ProcessingStage", back_populates="fallback_policies")


class ConfigurationChangeEvent(Base):
    """Audit events for configuration changes."""

    __tablename__ = "configuration_change_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("module_configurations.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    result: Mapped[str] = mapped_column(String(60), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    configuration: Mapped[ModuleConfiguration] = relationship(
        "ModuleConfiguration", back_populates="events"
    )
