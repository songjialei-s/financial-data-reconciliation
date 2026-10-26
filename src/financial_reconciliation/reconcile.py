from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .normalize import normalize_date, normalize_text, parse_decimal, protect_identifier
from .rules import SUPPORTED_RULES, key_fields


@dataclass(frozen=True)
class ReconciliationOutput:
    results: pd.DataFrame
    quality_issues: pd.DataFrame
    ledger_events: pd.DataFrame


def _money_cents(value: object) -> int | None:
    parsed = parse_decimal(value)
    return None if parsed is None else int(parsed * 100)


def _normalize_platform(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in (
        "platform_record_id", "account_id", "settlement_batch", "transaction_type",
        "order_id", "item_code", "marketplace", "currency", "status",
    ):
        result[column] = result[column].map(normalize_text)
    result["transaction_date"] = result["transaction_date"].map(normalize_date)
    result["release_date"] = result["release_date"].map(normalize_date)
    result["expected_cents"] = result["net_amount"].map(_money_cents)
    return result


def _normalize_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in (
        "ledger_entry_id", "event_id", "account_id", "settlement_batch",
        "transaction_type", "order_id", "item_code", "marketplace",
        "amount_category", "currency",
    ):
        result[column] = result[column].map(normalize_text)
    result["transaction_date"] = result["posting_date"].map(normalize_date)
    result["amount_cents"] = result["amount"].map(_money_cents)
    return result


def _quality_issues(platform: pd.DataFrame, ledger: pd.DataFrame) -> pd.DataFrame:
    issues: list[dict[str, str]] = []

    def add(source: str, record_id: str, issue: str, detail: str) -> None:
        issues.append(
            {"source": source, "record_id": record_id, "issue_type": issue, "detail": detail}
        )

    for _, row in platform.iterrows():
        tx_type = row["transaction_type"]
        fields = key_fields(tx_type)
        if fields is None:
            add("platform", row["platform_record_id"], "unsupported_transaction_type", tx_type)
        elif any(protect_identifier(row[field]) == "" for field in fields):
            add("platform", row["platform_record_id"], "missing_required_key", ",".join(fields))
        if row["transaction_date"] == "":
            add("platform", row["platform_record_id"], "invalid_date", "transaction_date")
        if row["expected_cents"] is None:
            add("platform", row["platform_record_id"], "invalid_amount", "net_amount")

    for duplicate_id in platform.loc[
        platform["platform_record_id"].duplicated(keep=False), "platform_record_id"
    ].unique():
        add("platform", duplicate_id, "duplicate_record_id", "platform_record_id")

    for duplicate_id in ledger.loc[
        ledger["ledger_entry_id"].duplicated(keep=False), "ledger_entry_id"
    ].unique():
        add("ledger", duplicate_id, "duplicate_record_id", "ledger_entry_id")

    fingerprint = [
        "event_id", "account_id", "settlement_batch", "transaction_type", "order_id",
        "item_code", "marketplace", "transaction_date", "amount_category", "currency",
        "amount_cents",
    ]
    duplicate_mask = ledger.duplicated(fingerprint, keep="first")
    for _, row in ledger[duplicate_mask].iterrows():
        add("ledger", row["ledger_entry_id"], "exact_duplicate_ledger_row", row["event_id"])

    for _, row in ledger.iterrows():
        if row["transaction_date"] == "":
            add("ledger", row["ledger_entry_id"], "invalid_date", "posting_date")
        if row["amount_cents"] is None:
            add("ledger", row["ledger_entry_id"], "invalid_amount", "amount")

    return pd.DataFrame(issues, columns=["source", "record_id", "issue_type", "detail"])


def _aggregate_ledger(ledger: pd.DataFrame) -> tuple[pd.DataFrame, set[str]]:
    fingerprint = [
        "event_id", "account_id", "settlement_batch", "transaction_type", "order_id",
        "item_code", "marketplace", "transaction_date", "amount_category", "currency",
        "amount_cents",
    ]
    duplicate_ids = set(
        ledger.loc[ledger.duplicated(fingerprint, keep="first"), "ledger_entry_id"]
    )
    usable = ledger[
        ~ledger["ledger_entry_id"].isin(duplicate_ids)
        & ledger["amount_cents"].notna()
        & ledger["transaction_date"].ne("")
    ].copy()
    group_columns = [
        "event_id", "account_id", "settlement_batch", "transaction_type", "order_id",
        "item_code", "marketplace", "transaction_date", "currency",
    ]
    events = usable.groupby(group_columns, dropna=False, as_index=False).agg(
        ledger_cents=("amount_cents", "sum"),
        ledger_line_count=("ledger_entry_id", "count"),
    )
    return events, duplicate_ids


def _key(row: pd.Series, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row[field]) for field in fields)


def reconcile(platform_raw: pd.DataFrame, ledger_raw: pd.DataFrame) -> ReconciliationOutput:
    platform = _normalize_platform(platform_raw)
    ledger = _normalize_ledger(ledger_raw)
    quality = _quality_issues(platform, ledger)
    events, _ = _aggregate_ledger(ledger)

    event_index: dict[tuple[str, tuple[str, ...]], list[int]] = defaultdict(list)
    for idx, row in events.iterrows():
        fields = key_fields(row["transaction_type"])
        if fields and all(str(row[field]) != "" for field in fields):
            event_index[(row["transaction_type"], _key(row, fields))].append(idx)

    consumed_events: set[str] = set()
    results: list[dict[str, object]] = []

    for _, row in platform.iterrows():
        tx_type = row["transaction_type"]
        fields = key_fields(tx_type)
        base = {
            "platform_record_id": row["platform_record_id"],
            "ledger_event_id": "",
            "transaction_type": tx_type,
            "business_key": "",
            "platform_currency": row["currency"],
            "ledger_currency": "",
            "platform_amount": _format_cents(row["expected_cents"]),
            "ledger_amount": "",
            "difference_amount": "",
            "candidate_count": 0,
            "ledger_line_count": 0,
            "result_type": "",
            "reason": "",
        }
        if fields is None:
            base.update(result_type="unsupported_rule", reason="No configured business-key rule")
            results.append(base)
            continue
        missing = [field for field in fields if str(row[field]) == ""]
        if missing or row["expected_cents"] is None or row["transaction_date"] == "":
            base.update(
                result_type="invalid_key",
                reason="Missing or invalid required field: " + ", ".join(missing or ["amount/date"]),
            )
            results.append(base)
            continue

        candidate_key = _key(row, fields)
        base["business_key"] = " | ".join(candidate_key)
        candidate_indices = event_index.get((tx_type, candidate_key), [])
        base["candidate_count"] = len(candidate_indices)
        for idx in candidate_indices:
            consumed_events.add(events.at[idx, "event_id"])
        if not candidate_indices:
            base.update(result_type="platform_only", reason="No ledger candidate for the business key")
            results.append(base)
            continue
        if len(candidate_indices) > 1:
            base.update(
                ledger_event_id=" | ".join(events.loc[candidate_indices, "event_id"]),
                result_type="ambiguous_candidate",
                reason="Multiple ledger events share the same business key",
            )
            results.append(base)
            continue

        candidate = events.loc[candidate_indices[0]]
        base.update(
            ledger_event_id=candidate["event_id"],
            ledger_currency=candidate["currency"],
            ledger_amount=_format_cents(candidate["ledger_cents"]),
            ledger_line_count=int(candidate["ledger_line_count"]),
        )
        if row["currency"] != candidate["currency"]:
            base.update(result_type="currency_mismatch", reason="Candidate currencies differ")
        else:
            difference = int(row["expected_cents"]) - int(candidate["ledger_cents"])
            base["difference_amount"] = _format_cents(difference)
            if difference == 0:
                base.update(result_type="matched", reason="Business key, currency, and amount agree")
            else:
                base.update(result_type="amount_mismatch", reason="Business key and currency agree; amount differs")
        results.append(base)

    # Add reverse-side exceptions for unconsumed ledger events.
    for _, event in events[~events["event_id"].isin(consumed_events)].iterrows():
        fields = key_fields(event["transaction_type"])
        if fields is None:
            continue
        results.append(
            {
                "platform_record_id": "",
                "ledger_event_id": event["event_id"],
                "transaction_type": event["transaction_type"],
                "business_key": " | ".join(_key(event, fields)),
                "platform_currency": "",
                "ledger_currency": event["currency"],
                "platform_amount": "",
                "ledger_amount": _format_cents(event["ledger_cents"]),
                "difference_amount": "",
                "candidate_count": 0,
                "ledger_line_count": int(event["ledger_line_count"]),
                "result_type": "ledger_only",
                "reason": "Ledger event has no platform record with the business key",
            }
        )

    return ReconciliationOutput(pd.DataFrame(results), quality, events)


def _format_cents(cents: object) -> str:
    if cents is None or pd.isna(cents):
        return ""
    return format(Decimal(int(cents)) / Decimal("100"), ".2f")


def load_and_reconcile(platform_path: Path, ledger_path: Path) -> ReconciliationOutput:
    platform = pd.read_csv(platform_path, dtype=str, keep_default_na=False)
    ledger = pd.read_csv(ledger_path, dtype=str, keep_default_na=False)
    return reconcile(platform, ledger)

