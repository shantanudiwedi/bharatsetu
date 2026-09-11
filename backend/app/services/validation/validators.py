import re
from decimal import Decimal, InvalidOperation
from typing import Optional


GST_STATE_CODES = frozenset(
    {
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
        "21", "22", "23", "24", "26", "27", "28", "29", "30", "31",
        "32", "33", "34", "35", "36", "37", "38", "97",
    }
)
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
GST_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")
UDYAM_RE = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$")
EPFO_ESTABLISHMENT_RE = re.compile(r"^[A-Z]{2}[A-Z]{3}[0-9]{10}$")
EPFO_NORMALIZED_RE = re.compile(r"^[A-Z0-9]{5,30}$")
PHONE_RE = re.compile(r"^[6-9][0-9]{9}$")
PIN_RE = re.compile(r"^[1-9][0-9]{5}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ENTITY_RE = re.compile(r"^[A-Za-z0-9\s&.,'()\-]+$")


def normalize_identifier(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return re.sub(r"\s+", "", value).upper()


def validate_entity_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", (value or "").strip())
    if not 2 <= len(normalized) <= 150 or not ENTITY_RE.fullmatch(normalized):
        raise ValueError("Enter a valid vendor/entity name.")
    if not re.search(r"[A-Za-z0-9]", normalized):
        raise ValueError("Enter a valid vendor/entity name.")
    return normalized


def validate_pan(value: str) -> str:
    normalized = normalize_identifier(value)
    if not normalized or not PAN_RE.fullmatch(normalized):
        raise ValueError("Invalid PAN format. Expected 10 characters (AAAAA9999A).")
    return normalized


def gstin_checksum_valid(gstin: str) -> bool:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    factor = 1
    total = 0
    for char in reversed(gstin[:14]):
        value = chars.index(char) * factor
        total += (value // 36) + (value % 36)
        factor = 1 if factor == 2 else 2
    return chars[(36 - (total % 36)) % 36] == gstin[14]


def validate_gstin(value: str, pan: Optional[str] = None) -> str:
    normalized = normalize_identifier(value)
    if not normalized or not GST_RE.fullmatch(normalized):
        raise ValueError("GSTIN must contain exactly 15 valid characters.")
    if normalized[:2] not in GST_STATE_CODES:
        raise ValueError("GSTIN contains an invalid state code.")
    if not gstin_checksum_valid(normalized):
        raise ValueError("GSTIN check digit is invalid.")
    if pan and normalized[2:12] != validate_pan(pan):
        raise ValueError("GSTIN does not match the entered PAN.")
    return normalized


def validate_udyam(value: str) -> str:
    normalized = (value or "").strip().upper()
    if not UDYAM_RE.fullmatch(normalized):
        raise ValueError("Invalid Udyam number. Expected UDYAM-XX-00-0000000.")
    return normalized


def validate_epfo(value: str) -> str:
    normalized = normalize_identifier(value)
    if not normalized or not (
        EPFO_ESTABLISHMENT_RE.fullmatch(normalized)
        or EPFO_NORMALIZED_RE.fullmatch(normalized)
    ):
        raise ValueError("Invalid EPFO identifier format.")
    return normalized


def parse_bid_amount(value: str) -> str:
    raw = str(value or "").strip().replace("₹", "").replace(",", "").replace(" ", "")
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError("Bid amount must be a valid INR number greater than ₹0.")
    if not amount.is_finite() or amount <= 0 or amount > Decimal("1000000000000"):
        raise ValueError("Bid amount must be finite, greater than ₹0, and within the allowed limit.")
    return format(amount, "f")


def normalize_name(value: Optional[str]) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def compare_names(left: Optional[str], right: Optional[str]) -> str:
    left_normalized = normalize_name(left)
    right_normalized = normalize_name(right)
    if not left_normalized or not right_normalized:
        return "UNVERIFIABLE"
    if left_normalized == right_normalized:
        return "MATCH"
    if left_normalized in right_normalized or right_normalized in left_normalized:
        return "PARTIAL_MATCH"
    return "MISMATCH"


def validate_phone(value: str) -> str:
    normalized = re.sub(r"\s+", "", value or "")
    if not PHONE_RE.fullmatch(normalized) or len(set(normalized)) == 1:
        raise ValueError("Enter a valid Indian mobile number.")
    return normalized


def validate_email(value: str) -> str:
    normalized = (value or "").strip().lower()
    if not EMAIL_RE.fullmatch(normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def validate_pin(value: str) -> str:
    normalized = (value or "").strip()
    if not PIN_RE.fullmatch(normalized):
        raise ValueError("Enter a valid six-digit PIN code.")
    return normalized
