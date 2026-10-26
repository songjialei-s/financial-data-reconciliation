DROP TABLE IF EXISTS platform_transactions;
DROP TABLE IF EXISTS ledger_entries;

CREATE TABLE platform_transactions (
    platform_record_id TEXT PRIMARY KEY,
    account_id TEXT,
    settlement_batch TEXT,
    transaction_type TEXT NOT NULL,
    order_id TEXT,
    item_code TEXT,
    marketplace TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    release_date TEXT NOT NULL,
    currency TEXT NOT NULL,
    gross_amount TEXT NOT NULL,
    tax_amount TEXT NOT NULL,
    fee_amount TEXT NOT NULL,
    net_amount TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE ledger_entries (
    ledger_entry_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    account_id TEXT,
    settlement_batch TEXT,
    transaction_type TEXT NOT NULL,
    order_id TEXT,
    item_code TEXT,
    marketplace TEXT NOT NULL,
    posting_date TEXT NOT NULL,
    amount_category TEXT NOT NULL,
    currency TEXT NOT NULL,
    amount TEXT NOT NULL
);

CREATE INDEX idx_platform_order_item
    ON platform_transactions(order_id, item_code, marketplace, transaction_type);
CREATE INDEX idx_ledger_order_item
    ON ledger_entries(order_id, item_code, marketplace, transaction_type);
CREATE INDEX idx_ledger_event ON ledger_entries(event_id);

