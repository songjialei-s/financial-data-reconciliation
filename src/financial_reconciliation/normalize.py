from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable

import pandas as pd


CENT = Decimal("0.01")


def protect_identifier(value: object) -> str:
    """Return an identifier as text without float conversion or rounding."""
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.startswith("'"):
        text = text[1:].strip()
    return text


def normalize_text(value: object) -> str:
    return protect_identifier(value).upper()


def parse_decimal(value: object) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None


def decimal_to_text(value: Decimal | None) -> str:
    return "" if value is None else format(value.quantize(CENT), "f")


def normalize_date(value: object) -> str:
    if value is None or str(value).strip() == "":
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def required_key_missing(values: Iterable[object]) -> bool:
    return any(protect_identifier(value) == "" for value in values)

