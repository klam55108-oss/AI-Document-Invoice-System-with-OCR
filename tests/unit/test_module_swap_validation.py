"""Unit tests for module swap validation."""

from core.configuration_validation import validate_configuration_payload


def test_module_swap_same_contract_allowed() -> None:
    """Swapping modules with matching contracts should validate."""
    payload = {
        "selections": [
            {"stage_id": "ocr", "module_id": "ocr-v2"},
        ]
    }
    required_stage_ids = {"ocr"}
    stage_contracts = {"ocr": "contract-ocr"}
    module_contracts = {"ocr-v2": "contract-ocr"}

    result = validate_configuration_payload(
        payload=payload,
        required_stage_ids=required_stage_ids,
        stage_contracts=stage_contracts,
        module_contracts=module_contracts,
    )

    assert result.is_valid is True
