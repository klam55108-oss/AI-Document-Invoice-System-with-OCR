"""Configuration service for module selection and activation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, UTC

from core.configuration_validation import ValidationResult, validate_configuration_payload
from core.module_registry import module_contract_map, required_stage_ids, stage_contract_map
from core.observability import record_event, record_metric


@dataclass(slots=True)
class ConfigurationRecord:
    """In-memory configuration record for service operations."""

    config_id: str
    version: str
    status: str
    created_by: str
    created_at: datetime
    activated_at: datetime | None
    selections: list[dict]


@dataclass(slots=True)
class ActivationResult:
    """Activation or rollback outcome."""

    status: str
    message: str


class ConfigurationService:
    """Service for configuration lifecycle management."""

    def __init__(self) -> None:
        self._configs: dict[str, ConfigurationRecord] = {}
        self._events: list[dict] = []
        self._active_config_id: str | None = None
        self._pending_activation_id: str | None = None
        self._version_counter = 0
        self._fallback_policies: dict[str, str] = {}

    async def create_configuration(self, selections: list[dict], created_by: str) -> ConfigurationRecord:
        """Create a new configuration draft."""
        self._version_counter += 1
        config_id = str(uuid.uuid4())
        record = ConfigurationRecord(
            config_id=config_id,
            version=f"v{self._version_counter}",
            status="draft",
            created_by=created_by,
            created_at=datetime.now(UTC),
            activated_at=None,
            selections=selections,
        )
        self._configs[config_id] = record
        self._events.append(
            {"action": "create", "config_id": config_id, "actor": created_by, "result": "ok"}
        )
        record_event("config_created", config_id=config_id, actor=created_by)
        return record

    async def validate_configuration(self, selections: list[dict]) -> ValidationResult:
        """Validate configuration selections against registry metadata."""
        payload = {"selections": selections}
        result = validate_configuration_payload(
            payload=payload,
            required_stage_ids=required_stage_ids(),
            stage_contracts=stage_contract_map(),
            module_contracts=module_contract_map(),
        )
        record_metric("config_validation", 1, outcome="valid" if result.is_valid else "invalid")
        return result

    async def activate_configuration(
        self, config_id: str, has_active_processing: bool
    ) -> ActivationResult:
        """Activate configuration now or queue if processing is active."""
        if config_id not in self._configs:
            return ActivationResult(status="rejected", message="Configuration not found")

        if has_active_processing:
            self._pending_activation_id = config_id
            self._events.append(
                {"action": "activate", "config_id": config_id, "result": "queued"}
            )
            record_event("config_activation_queued", config_id=config_id)
            return ActivationResult(status="queued", message="Activation queued")

        self._set_active_config(config_id)
        record_event("config_activation_applied", config_id=config_id)
        return ActivationResult(status="queued", message="Activation applied")

    async def rollback_configuration(
        self, config_id: str, actor: str, has_active_processing: bool
    ) -> ActivationResult:
        """Rollback by creating a new configuration version from prior selections."""
        if config_id not in self._configs:
            return ActivationResult(status="rejected", message="Configuration not found")

        target = self._configs[config_id]
        new_record = await self.create_configuration(
            selections=target.selections, created_by=actor
        )

        if has_active_processing:
            self._pending_activation_id = new_record.config_id
            self._events.append(
                {"action": "rollback", "config_id": new_record.config_id, "result": "queued"}
            )
            record_event("config_rollback_queued", config_id=new_record.config_id, actor=actor)
            return ActivationResult(status="queued", message="Rollback queued")

        self._set_active_config(new_record.config_id)
        record_event("config_rollback_applied", config_id=new_record.config_id, actor=actor)
        return ActivationResult(status="queued", message="Rollback applied")

    async def get_active_configuration(self) -> ConfigurationRecord | None:
        """Return the active configuration record."""
        if not self._active_config_id:
            return None
        return self._configs.get(self._active_config_id)

    def get_pending_activation(self) -> str | None:
        """Return pending activation config ID, if any."""
        return self._pending_activation_id

    async def list_configurations(self) -> list[ConfigurationRecord]:
        """Return all configuration records."""
        return list(self._configs.values())

    async def get_configuration(self, config_id: str) -> ConfigurationRecord | None:
        """Return a configuration by ID."""
        return self._configs.get(config_id)

    async def set_fallback_policy(self, stage_id: str, fallback_module_id: str) -> None:
        """Define fallback module for a stage."""
        self._fallback_policies[stage_id] = fallback_module_id
        self._events.append(
            {
                "action": "set_fallback",
                "stage_id": stage_id,
                "fallback_module_id": fallback_module_id,
                "result": "ok",
            }
        )
        record_event(
            "fallback_policy_set",
            stage_id=stage_id,
            fallback_module_id=fallback_module_id,
        )

    async def evaluate_fallback(self, stage_id: str, error: str) -> str | None:
        """Return fallback module ID for stage if configured."""
        fallback_module_id = self._fallback_policies.get(stage_id)
        if fallback_module_id:
            record_metric("fallback_used", 1, stage_id=stage_id)
            record_event(
                "fallback_selected",
                stage_id=stage_id,
                fallback_module_id=fallback_module_id,
                error=error,
            )
        return fallback_module_id

    def _set_active_config(self, config_id: str) -> None:
        """Set active configuration and supersede previous."""
        if self._active_config_id and self._active_config_id in self._configs:
            previous = self._configs[self._active_config_id]
            previous.status = "superseded"
            self._events.append(
                {
                    "action": "swap",
                    "config_id": config_id,
                    "previous_config_id": previous.config_id,
                    "result": "ok",
                }
            )
            record_event(
                "config_swapped",
                config_id=config_id,
                previous_config_id=previous.config_id,
            )

        record = self._configs[config_id]
        record.status = "active"
        record.activated_at = datetime.now(UTC)
        self._active_config_id = config_id
        self._pending_activation_id = None


_service = ConfigurationService()


def get_configuration_service() -> ConfigurationService:
    """Return shared configuration service instance."""
    return _service
