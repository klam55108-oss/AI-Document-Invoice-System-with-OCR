"""Configuration validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationResult:
    """Validation outcome for a configuration payload."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_configuration_payload(
    payload: dict,
    required_stage_ids: set[str],
    stage_contracts: dict[str, str],
    module_contracts: dict[str, str],
) -> ValidationResult:
    """Validate configuration payload against required stages and contracts."""
    errors: list[str] = []
    warnings: list[str] = []
    selections = payload.get("selections") or []

    stage_ids = [selection.get("stage_id") for selection in selections]
    missing = required_stage_ids.difference(stage_ids)
    if missing:
        errors.append(f"Missing required stages: {', '.join(sorted(missing))}")

    duplicates = {stage_id for stage_id in stage_ids if stage_ids.count(stage_id) > 1}
    if duplicates:
        errors.append(f"Duplicate stage selections: {', '.join(sorted(duplicates))}")

    for selection in selections:
        stage_id = selection.get("stage_id")
        module_id = selection.get("module_id")
        if not stage_id or not module_id:
            errors.append("Selection missing stage_id or module_id")
            continue
        stage_contract = stage_contracts.get(stage_id)
        module_contract = module_contracts.get(module_id)
        if stage_contract and module_contract and stage_contract != module_contract:
            errors.append(
                f"Module {module_id} contract {module_contract} does not match stage {stage_id}"
            )
        if stage_contract and module_contract is None:
            warnings.append(f"Module {module_id} has no contract metadata")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
