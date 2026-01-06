"""Unit tests for filter utilities."""

import pytest

from interface.dashboard.utils.filters import validate_filter_state


def test_validate_filter_state_valid():
    """Test filter state validation with valid filters."""
    filters = {
        "amount_min": 100.0,
        "amount_max": 1000.0,
        "confidence_min": 0.8,
        "vendor": "Test Vendor",
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is True
    assert error is None


def test_validate_filter_state_amount_min_greater_than_max():
    """Test filter state validation when amount_min > amount_max."""
    filters = {
        "amount_min": 1000.0,
        "amount_max": 100.0,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is False
    assert "Minimum amount must be less than or equal to maximum amount" in error


def test_validate_filter_state_negative_amount_min():
    """Test filter state validation with negative amount_min."""
    filters = {
        "amount_min": -100.0,
        "amount_max": 1000.0,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is False
    assert "Minimum amount cannot be negative" in error


def test_validate_filter_state_negative_amount_max():
    """Test filter state validation with negative amount_max."""
    filters = {
        "amount_min": 100.0,
        "amount_max": -100.0,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is False
    assert "Maximum amount cannot be negative" in error


def test_validate_filter_state_confidence_below_zero():
    """Test filter state validation with confidence below 0.0."""
    filters = {
        "confidence_min": -0.1,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is False
    assert "Confidence must be between 0.0 and 1.0" in error


def test_validate_filter_state_confidence_above_one():
    """Test filter state validation with confidence above 1.0."""
    filters = {
        "confidence_min": 1.5,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is False
    assert "Confidence must be between 0.0 and 1.0" in error


def test_validate_filter_state_confidence_valid():
    """Test filter state validation with valid confidence."""
    filters = {
        "confidence_min": 0.85,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is True
    assert error is None


def test_validate_filter_state_empty():
    """Test filter state validation with empty filters."""
    filters = {}
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is True
    assert error is None


def test_validate_filter_state_only_amount_min():
    """Test filter state validation with only amount_min."""
    filters = {
        "amount_min": 100.0,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is True
    assert error is None


def test_validate_filter_state_only_amount_max():
    """Test filter state validation with only amount_max."""
    filters = {
        "amount_max": 1000.0,
    }
    
    is_valid, error = validate_filter_state(filters)
    
    assert is_valid is True
    assert error is None


def test_validate_filter_state_combination_logic():
    """Test filter state validation with multiple valid combinations."""
    # Test various valid combinations
    test_cases = [
        {"amount_min": 0.0, "amount_max": 1000.0, "confidence_min": 0.0},
        {"amount_min": 100.0, "amount_max": 100.0, "confidence_min": 1.0},
        {"vendor": "Test", "confidence_min": 0.5},
        {"amount_min": 50.0, "confidence_min": 0.75},
    ]
    
    for filters in test_cases:
        is_valid, error = validate_filter_state(filters)
        assert is_valid is True, f"Filters {filters} should be valid"
        assert error is None

