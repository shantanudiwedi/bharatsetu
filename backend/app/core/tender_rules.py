from typing import Any

MIN_TENDER_VALUE_INR = 100000.0


def format_inr(value: Any) -> str:
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return "₹0"
    sign = "-" if amount < 0 else ""
    amount = abs(amount)

    s = str(amount)
    last_three = s[-3:]
    rest = s[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    formatted = ",".join(groups) + "," + last_three if groups else last_three
    return f"{sign}₹{formatted}"


def tender_value_is_eligible(value: Any) -> bool:
    if value is None:
        return False
    try:
        return float(value) >= MIN_TENDER_VALUE_INR
    except (TypeError, ValueError):
        return False


def is_tender_above_minimum_value(tender: Any) -> bool:
    if tender is None:
        return False
    return tender_value_is_eligible(getattr(tender, "estimated_value", None))


def is_tender_live_and_eligible(tender: Any) -> bool:
    if tender is None:
        return False
    if str(getattr(tender, "status", "")).upper() != "ACTIVE":
        return False
    return is_tender_above_minimum_value(tender)
