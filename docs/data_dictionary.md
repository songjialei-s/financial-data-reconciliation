# Data dictionary / 数据字典

All fields are fictional and designed for this portfolio project.

## Platform transactions / 平台交易

| Field | Meaning |
|---|---|
| `platform_record_id` | Synthetic source record identifier |
| `account_id` | Synthetic merchant account identifier |
| `settlement_batch` | Synthetic settlement grouping |
| `transaction_type` | Generic transaction category |
| `order_id` | Synthetic order identifier where applicable |
| `item_code` | Synthetic item identifier where applicable |
| `marketplace` | Fictional operating region |
| `transaction_date` | Business transaction date |
| `release_date` | Fictional release date |
| `currency` | ISO-style demonstration currency |
| `gross_amount` | Base transaction amount |
| `tax_amount` | Synthetic tax component |
| `fee_amount` | Synthetic fee component |
| `net_amount` | Amount expected to reconcile |
| `status` | Fictional processing status |

## Ledger entries / 账务明细

| Field | Meaning |
|---|---|
| `ledger_entry_id` | Unique ledger row identifier |
| `event_id` | Event grain used before candidate matching |
| Business-key fields | Generic account, batch, transaction, order, item, marketplace, and date fields |
| `amount_category` | Generic component label: base, tax, or service |
| `currency` | Ledger event currency |
| `amount` | Component amount stored as decimal text in CSV and SQLite |

## Reconciliation results / 核查结果

Each result retains source identifiers, event identifiers, normalized business key, currencies, amounts, candidate count, ledger line count, result classification, and a readable reason.

