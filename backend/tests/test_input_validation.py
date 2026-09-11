import pytest

from app.services.validation.validators import (
    compare_names,
    parse_bid_amount,
    validate_entity_name,
    validate_gstin,
    validate_pan,
    validate_udyam,
)


def test_pan_normalizes_and_rejects_invalid_values():
    assert validate_pan("abcde1234f") == "ABCDE1234F"
    for value in ("1234567890", "ABCDE12345", "ABCD12345F", "ABCDE1234"):
        with pytest.raises(ValueError):
            validate_pan(value)


def test_gstin_checks_structure_state_checksum_and_pan():
    assert validate_gstin("27abcde1234f1z5", "abcde1234f") == "27ABCDE1234F1Z5"
    with pytest.raises(ValueError, match="state"):
        validate_gstin("00ABCDE1234F1Z5", "ABCDE1234F")
    with pytest.raises(ValueError, match="PAN"):
        validate_gstin("27ABCDE1234F1Z5", "AAAPA1234A")
    with pytest.raises(ValueError, match="check digit"):
        validate_gstin("27ABCDE1234F1Z6", "ABCDE1234F")


def test_udyam_entity_amount_and_name_consistency_validation():
    assert validate_udyam("udyam-mh-29-0048291") == "UDYAM-MH-29-0048291"
    assert validate_entity_name("ABC & Sons") == "ABC & Sons"
    assert compare_names("Shree Ganesh Engineering Pvt. Ltd.", "Shree Ganesh Engineering Pvt Ltd") == "MATCH"
    assert parse_bid_amount("12,34,567") == "1234567"
    for value in ("", "   ", "@@@"):
        with pytest.raises(ValueError):
            validate_entity_name(value)
    for value in ("0", "-5000", "NaN", "Infinity"):
        with pytest.raises(ValueError):
            parse_bid_amount(value)
    with pytest.raises(ValueError):
        validate_udyam("UDYAM-MH-29-123")
