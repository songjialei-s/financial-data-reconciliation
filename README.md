# Financial Data Reconciliation

[English](#english) | [中文](#中文)

![Reconciliation results](reports/figures/reconciliation_results.png)

## English

### Project overview

This portfolio project demonstrates an end-to-end financial data reconciliation workflow for a fictional marketplace. It compares a platform transaction extract with an internal ledger, aligns different data grains, applies transaction-specific business keys, validates currency and amount, and produces traceable exception reports.

All data is deterministic and synthetic. The project contains no employer data, customer data, production credentials, internal system names, or proprietary mapping rules.

### Business problem

Platform reports often store one net transaction per row, while an accounting or operational ledger can split the same event across several amount lines. A direct row-to-row join can double-count values, miss valid one-to-many relationships, or create false matches based only on similar amounts.

This project uses the following sequence:

1. Normalize identifiers, dates, text, currencies, and decimal amounts.
2. Check missing keys, invalid values, unsupported types, and exact duplicates.
3. Aggregate ledger lines to the event grain.
4. Find candidates using a configured business key for each transaction type.
5. Validate candidate count, currency, and amount in that order.
6. Add reverse-side ledger exceptions that have no platform record.
7. Export reasons, identifiers, candidate counts, and amounts for audit.

### Technology stack

- Python 3.10+
- Pandas
- SQLite and SQL
- `decimal.Decimal` for financial amounts
- Matplotlib
- Pytest
- CSV and Excel reporting

### Data model and grain

| Dataset | Grain | Example role |
|---|---|---|
| `platform_transactions` | One platform transaction record | Source-side net transaction |
| `ledger_entries` | One amount component within a ledger event | One-to-many accounting detail |
| Aggregated ledger events | One `event_id` and business key | Candidate used for reconciliation |
| `reconciliation_results` | One platform decision, plus unmatched ledger events | Final auditable result |

Generic transaction rules:

| Transaction type | Candidate business key |
|---|---|
| `SALE`, `REFUND` | order ID + item code + marketplace + transaction type |
| `ADJUSTMENT` | item code + marketplace + transaction type + transaction date |
| `ACCOUNT_FEE` | account ID + marketplace + transaction type + settlement batch |

Amount is never used to identify a transaction. It is checked only after the business-key candidate is selected.

### Result classifications

- `matched`
- `amount_mismatch`
- `currency_mismatch`
- `platform_only`
- `ledger_only`
- `ambiguous_candidate`
- `invalid_key`
- `unsupported_rule`

### Synthetic run results

The committed example was generated with seed `20261026`.

| Metric | Result |
|---|---:|
| Platform transactions | 6,000 |
| Ledger detail rows | 9,771 |
| Aggregated ledger events | 5,676 |
| Reconciliation decisions | 6,300 |
| Matched | 4,417 |
| Amount mismatch | 295 |
| Currency mismatch | 188 |
| Platform only | 280 |
| Ledger only | 300 |
| Ambiguous candidate | 320 |
| Invalid key | 171 |
| Unsupported rule | 329 |

The 6,300 decisions equal 6,000 platform decisions plus 300 reverse-side ledger-only events. Exact duplicate ledger rows are reported as data-quality issues and explicitly excluded from event aggregation.

![Result distribution](reports/figures/reconciliation_share.png)

![Data quality issues](reports/figures/data_quality_issues.png)

### Repository outputs

- `reports/reconciliation_results.csv`: complete traceable decision set
- `reports/reconciliation_summary.csv`: result counts and shares
- `reports/data_quality_issues.csv`: row-level quality exceptions
- `reports/data_quality_summary.csv`: quality issue counts
- `reports/reconciliation_report.xlsx`: formatted summary, full detail, quality issues, and methodology
- `data/generated/*.csv`: deterministic synthetic source data and injected-scenario truth labels

### Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m financial_reconciliation.cli all --root . --rows 6000 --seed 20261026
pytest
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

The standard CLI regenerates synthetic CSV data, SQLite tables, reconciliation CSV files, and PNG charts. The formatted example Excel workbook is included as a portfolio output.

### Test result

The final local run completed with:

```text
14 passed in 0.86s
```

Tests cover identifier precision, decimal arithmetic, one-to-many aggregation, amount and currency checks, ambiguous candidates, bidirectional missing records, duplicate handling, unsupported rules, and result-count conservation.

### Known limitations

- This is an analytical demonstration, not a production accounting control.
- Business keys are intentionally generic and simplified.
- The project does not implement foreign-exchange conversion.
- Date tolerances and settlement-period carry-forwards are not modeled.
- The SQLite demo is single-process and not designed for production scale.
- Synthetic scenario proportions are designed for visibility, not to represent a real business distribution.

### Privacy

The generator creates every identifier and amount from code using a fixed random seed. It does not read an external dataset, database, API, shared drive, or confidential project folder. See [Privacy and synthetic data](docs/privacy_and_synthetic_data.md).

---

## 中文

### 项目概述

本项目使用完全合成的Marketplace交易和内部账务数据，演示从多源标准化、数据粒度对齐、业务键候选匹配、币种与金额验证，到差异分类和异常追溯的完整流程。

项目不包含任何雇主、客户、平台账户、生产数据库、内部系统名称或专有费用映射规则。

### 业务问题

平台报表通常以一行净额表示一笔交易，内部账务系统则可能把同一事件拆成多条金额组件。直接逐行连接可能导致重复计数、遗漏一对多关系，或仅凭相同金额产生误匹配。

本项目按以下顺序处理：

1. 标准化ID、日期、文本、币种和Decimal金额。
2. 检查缺失业务键、无效值、未知类型和账务重复行。
3. 先把一对多账务明细聚合到事件粒度。
4. 根据交易类型使用不同业务键寻找候选。
5. 依次验证候选数量、币种和金额。
6. 反向识别只有账务记录、没有平台记录的事件。
7. 输出记录ID、业务键、候选数量、金额及异常原因。

### 数据结构与粒度

| 数据集 | 粒度 |
|---|---|
| 平台交易表 | 一行一笔平台交易净额 |
| 内部账务表 | 一行一个账务金额组件 |
| 账务事件聚合层 | 一行一个`event_id`及业务键 |
| 核查结果 | 一行一个平台判断，并追加账务单边事件 |

通用匹配规则：

| 交易类型 | 候选业务键 |
|---|---|
| 销售、退款 | 订单ID + 商品编码 + Marketplace + 交易类型 |
| 调整 | 商品编码 + Marketplace + 交易类型 + 交易日期 |
| 账户费用 | 账户ID + Marketplace + 交易类型 + 结算批次 |

金额不用于寻找候选，只在业务键候选确定后进行验证。

### 差异分类

- 完全匹配 `matched`
- 金额差异 `amount_mismatch`
- 币种差异 `currency_mismatch`
- 仅平台存在 `platform_only`
- 仅账务存在 `ledger_only`
- 多候选歧义 `ambiguous_candidate`
- 业务键无效 `invalid_key`
- 未配置规则 `unsupported_rule`

### 合成数据结果

固定随机种子`20261026`生成：

- 6,000条平台交易
- 9,771条账务明细
- 5,676个账务事件
- 6,300条双向核查结果
- 4,417条完全匹配
- 295条金额差异
- 188条币种差异
- 280条仅平台存在
- 300条仅账务存在
- 320条多候选歧义
- 171条无效业务键
- 329条未配置规则

6,300条结果由6,000条平台侧判断和300条账务单边事件组成。62条完全重复的账务明细被单独记录为数据质量问题，并在事件聚合时明确排除。

### 运行方式

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m financial_reconciliation.cli all --root . --rows 6000 --seed 20261026
pytest
```

### 测试结果

最终实际运行结果为：

```text
14 passed in 0.86s
```

测试覆盖ID精度、Decimal金额、一对多聚合、金额和币种验证、多候选、双向缺失、重复明细、未知规则及结果数量守恒。

### 已知限制

- 本项目是分析演示，不是生产会计控制。
- 业务键和交易类型经过通用化简化。
- 未实现外汇换算。
- 未实现跨期日期容差和结算批次结转。
- SQLite适合本地演示，不代表生产规模架构。
- 合成异常比例用于展示分类，不代表真实业务分布。

### 隐私说明

所有ID和金额均由代码使用固定随机种子生成。程序不会读取外部数据集、数据库、API、共享盘或任何保密项目目录。详细说明见[隐私与合成数据](docs/privacy_and_synthetic_data.md)。

