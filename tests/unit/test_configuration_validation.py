"""Unit tests for configuration validation."""

from core.configuration_validation import ValidationResult, validate_configuration_payload


def test_validate_missing_required_stage() -> None:
    """Reject configurations missing required stages."""
    payload = {
        "selections": [
            {"stage_id": "ocr", "module_id": "ocr-v1"},
        ]
    }
    required_stage_ids = {"ocr", "extract"}
    stage_contracts = {"ocr": "contract-ocr", "extract": "contract-extract"}
    module_contracts = {"ocr-v1": "contract-ocr"}

    result = validate_configuration_payload(
        payload=payload,
        required_stage_ids=required_stage_ids,
        stage_contracts=stage_contracts,
        module_contracts=module_contracts,
    )

    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert any("missing" in error for error in result.errors)


def test_validate_contract_mismatch() -> None:
    """Reject configurations when module contracts do not match stages."""
    payload = {
        "selections": [
            {"stage_id": "ocr", "module_id": "ocr-v2"},
        ]
    }
    required_stage_ids = {"ocr"}
    stage_contracts = {"ocr": "contract-ocr"}
    module_contracts = {"ocr-v2": "contract-legacy"}

    result = validate_configuration_payload(
        payload=payload,
        required_stage_ids=required_stage_ids,
        stage_contracts=stage_contracts,
        module_contracts=module_contracts,
    )

    assert result.is_valid is False
    assert any("contract" in error for error in result.errors)
