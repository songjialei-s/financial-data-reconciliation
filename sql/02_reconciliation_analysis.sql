-- Result distribution
SELECT
    result_type,
    COUNT(*) AS record_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM reconciliation_results
GROUP BY result_type
ORDER BY record_count DESC;

-- Amount differences by transaction type
SELECT
    transaction_type,
    COUNT(*) AS mismatch_count,
    ROUND(SUM(ABS(CAST(difference_amount AS REAL))), 2) AS absolute_difference
FROM reconciliation_results
WHERE result_type = 'amount_mismatch'
GROUP BY transaction_type
ORDER BY absolute_difference DESC;

-- Exceptions by transaction type and classification
SELECT
    transaction_type,
    result_type,
    COUNT(*) AS record_count
FROM reconciliation_results
WHERE result_type <> 'matched'
GROUP BY transaction_type, result_type
ORDER BY transaction_type, record_count DESC;

