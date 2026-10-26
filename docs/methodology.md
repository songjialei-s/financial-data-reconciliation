# Methodology / 核查方法

## 1. Normalize / 标准化

Identifiers remain strings. Dates use ISO `YYYY-MM-DD`. Amounts are parsed with `decimal.Decimal` and converted to integer cents for aggregation and equality checks.

## 2. Validate / 数据质量检查

The pipeline identifies missing business-key fields, invalid dates or amounts, unsupported transaction types, duplicate technical identifiers, and exact duplicate ledger content.

## 3. Align grain / 粒度对齐

Ledger component rows are aggregated by `event_id`, business-key fields, and currency. Exact duplicate content is reported and excluded explicitly rather than removed through an unexplained global `DISTINCT`.

## 4. Match candidates / 寻找候选

Each supported transaction type owns a business-key rule. Amount is excluded from the candidate key. This prevents a similar amount from being treated as proof that two records represent the same business event.

## 5. Verify and classify / 验证与分类

The engine checks candidate count, currency, and amount. More than one candidate becomes `ambiguous_candidate`; a unique candidate then proceeds to currency and amount validation.

## 6. Reverse-side check / 反向检查

Unconsumed ledger events are emitted as `ledger_only`, which makes the final result bidirectional rather than a source-only left join.

## 7. Conservation / 数量守恒

Every platform record receives exactly one decision. Each valid unconsumed ledger event receives one reverse-side decision. Ambiguous candidates are marked as consumed by the matching attempt so they are not incorrectly counted again as ledger-only exceptions.

