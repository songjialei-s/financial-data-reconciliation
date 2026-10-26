from __future__ import annotations

import pandas as pd


def platform_row(**overrides):
    row = {
        "platform_record_id": "PLT-0001",
        "account_id": "ACCT-001",
        "settlement_batch": "BATCH-001",
        "transaction_type": "SALE",
        "order_id": "ORD-00000001",
        "item_code": "ITEM-000001",
        "marketplace": "NORTH",
        "transaction_date": "2026-01-05",
        "release_date": "2026-01-06",
        "currency": "USD",
        "gross_amount": "10.00",
        "tax_amount": "0.70",
        "fee_amount": "-0.35",
        "net_amount": "10.35",
        "status": "RELEASED",
    }
    row.update(overrides)
    return row


def ledger_row(entry_id="LED-0001", event_id="EVT-0001", amount="10.35", **overrides):
    row = {
        "ledger_entry_id": entry_id,
        "event_id": event_id,
        "account_id": "ACCT-001",
        "settlement_batch": "BATCH-001",
        "transaction_type": "SALE",
        "order_id": "ORD-00000001",
        "item_code": "ITEM-000001",
        "marketplace": "NORTH",
        "posting_date": "2026-01-05",
        "amount_category": "BASE",
        "currency": "USD",
        "amount": amount,
    }
    row.update(overrides)
    return row


def frames(platform_rows, ledger_rows):
    return pd.DataFrame(platform_rows), pd.DataFrame(ledger_rows)

