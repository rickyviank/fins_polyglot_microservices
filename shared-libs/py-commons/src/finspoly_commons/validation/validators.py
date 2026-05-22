import re

_EMAIL = re.compile(r"^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_ACCOUNT_NUMBER = re.compile(r"^\d{10}$")
_E164 = re.compile(r"^\+[1-9]\d{6,14}$")
_US_SSN = re.compile(r"^\d{3}-?\d{2}-?\d{4}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")


def is_email(s: str | None) -> bool:
    return bool(s and _EMAIL.match(s))


def is_account_number(s: str | None) -> bool:
    return bool(s and _ACCOUNT_NUMBER.match(s))


def is_e164_phone(s: str | None) -> bool:
    return bool(s and _E164.match(s))


def is_us_ssn(s: str | None) -> bool:
    return bool(s and _US_SSN.match(s))


def is_currency_code(s: str | None) -> bool:
    return bool(s and _CURRENCY.match(s))


def is_luhn_valid(card_number: str | None) -> bool:
    if not card_number:
        return False
    digits = re.sub(r"\s+", "", card_number)
    if not re.fullmatch(r"\d{13,19}", digits):
        return False
    total = 0
    alt = False
    for ch in reversed(digits):
        n = ord(ch) - 48
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0
