from decimal import Decimal

from financial_reconciliation.normalize import normalize_date, parse_decimal, protect_identifier


def test_identifier_keeps_leading_zeroes_and_long_digits():
    identifier = "000123456789012345678901"
    assert protect_identifier(identifier) == identifier


def test_decimal_uses_exact_base_ten_arithmetic():
    assert parse_decimal("0.10") + parse_decimal("0.20") == Decimal("0.30")


def test_decimal_accepts_thousands_separator():
    assert parse_decimal("1,234.56") == Decimal("1234.56")


def test_date_normalization():
    assert normalize_date("2026/01/05") == "2026-01-05"
    assert normalize_date("not-a-date") == ""

