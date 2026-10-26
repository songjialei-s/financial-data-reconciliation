from __future__ import annotations


SUPPORTED_RULES: dict[str, tuple[str, ...]] = {
    "SALE": ("order_id", "item_code", "marketplace", "transaction_type"),
    "REFUND": ("order_id", "item_code", "marketplace", "transaction_type"),
    "ADJUSTMENT": ("item_code", "marketplace", "transaction_type", "transaction_date"),
    "ACCOUNT_FEE": ("account_id", "marketplace", "transaction_type", "settlement_batch"),
}


def key_fields(transaction_type: str) -> tuple[str, ...] | None:
    return SUPPORTED_RULES.get(transaction_type)

