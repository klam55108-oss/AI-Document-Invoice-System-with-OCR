"""Module registry for capability contracts and availability."""

from __future__ import annotations

from dataclasses import dataclass

from core.observability import record_event


@dataclass(slots=True)
class ModuleInfo:
    """In-memory module metadata."""

    module_id: str
    name: str
    stage_id: str
    capability_contract_id: str
    status: str
    is_fallback: bool = False


@dataclass(slots=True)
class StageInfo:
    """In-memory stage metadata."""

    stage_id: str
    name: str
    order: int
    capability_contract_id: str
    is_required: bool = True


@dataclass(slots=True)
class ContractInfo:
    """In-memory capability contract metadata."""

    contract_id: str
    name: str
    inputs: list[str]
    outputs: list[str]
    guarantees: list[str]


_modules: list[ModuleInfo] = []
_stages: list[StageInfo] = []
_contracts: list[ContractInfo] = []


def list_modules() -> list[ModuleInfo]:
    """Return registered modules."""
    return list(_modules)


def list_stages() -> list[StageInfo]:
    """Return registered stages."""
    return list(_stages)


def list_contracts() -> list[ContractInfo]:
    """Return registered capability contracts."""
    return list(_contracts)


def register_module(module: ModuleInfo) -> None:
    """Register a module definition."""
    _modules.append(module)


def register_stage(stage: StageInfo) -> None:
    """Register a processing stage."""
    _stages.append(stage)


def register_contract(contract: ContractInfo) -> None:
    """Register a capability contract."""
    _contracts.append(contract)


def check_module_availability(module_id: str) -> bool:
    """Return True when module is available in registry."""
    return any(module.module_id == module_id and module.status == "available" for module in _modules)


def resolve_startup_module(module_id: str, fallback_module_id: str | None = None) -> str | None:
    """Resolve module availability at startup, returning fallback if unavailable."""
    if check_module_availability(module_id):
        return module_id

    if fallback_module_id and check_module_availability(fallback_module_id):
        record_event(
            "module_startup_fallback",
            module_id=module_id,
            fallback_module_id=fallback_module_id,
        )
        return fallback_module_id

    record_event("module_startup_unavailable", module_id=module_id)
    return None


def module_contract_map() -> dict[str, str]:
    """Map module_id to contract_id."""
    return {module.module_id: module.capability_contract_id for module in _modules}


def stage_contract_map() -> dict[str, str]:
    """Map stage_id to contract_id."""
    return {stage.stage_id: stage.capability_contract_id for stage in _stages}


def required_stage_ids() -> set[str]:
    """Return required stage IDs."""
    return {stage.stage_id for stage in _stages if stage.is_required}
