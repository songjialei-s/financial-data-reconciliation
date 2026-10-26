-- Exact duplicate ledger content, excluding the technical row identifier
SELECT
    event_id,
    account_id,
    settlement_batch,
    transaction_type,
    order_id,
    item_code,
    marketplace,
    posting_date,
    amount_category,
    currency,
    amount,
    COUNT(*) AS duplicate_count
FROM ledger_entries
GROUP BY
    event_id, account_id, settlement_batch, transaction_type,
    order_id, item_code, marketplace, posting_date,
    amount_category, currency, amount
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Missing identifiers for order-level records
SELECT transaction_type, COUNT(*) AS missing_key_count
FROM platform_transactions
WHERE transaction_type IN ('SALE', 'REFUND')
  AND (TRIM(COALESCE(order_id, '')) = '' OR TRIM(COALESCE(item_code, '')) = '')
GROUP BY transaction_type;

-- Data quality issue summary populated by the Python pipeline
SELECT issue_type, COUNT(*) AS issue_count
FROM data_quality_issues
GROUP BY issue_type
ORDER BY issue_count DESC;

