from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


SCENARIOS = (
    ("matched", 0.75),
    ("amount_mismatch", 0.05),
    ("currency_mismatch", 0.03),
    ("platform_only", 0.05),
    ("ambiguous_candidate", 0.03),
    ("invalid_key", 0.03),
    ("unsupported_rule", 0.06),
)

MARKETPLACES = ("NORTH", "SOUTH", "WEST")
CURRENCIES = ("USD", "EUR", "GBP")
SUPPORTED_TYPES = ("SALE", "REFUND", "ADJUSTMENT", "ACCOUNT_FEE")
COMPONENTS = ("BASE", "TAX", "SERVICE")


@dataclass(frozen=True)
class GeneratedPaths:
    platform_csv: Path
    ledger_csv: Path
    truth_csv: Path


def money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def choose_scenario(rng: random.Random) -> str:
    point = rng.random()
    cumulative = 0.0
    for name, weight in SCENARIOS:
        cumulative += weight
        if point <= cumulative:
            return name
    return SCENARIOS[-1][0]


def split_amount(total: Decimal, rng: random.Random) -> list[Decimal]:
    part_count = rng.choices([1, 2, 3], weights=[42, 43, 15], k=1)[0]
    if part_count == 1:
        return [total]
    first_ratio = Decimal(str(rng.uniform(0.55, 0.88)))
    first = (total * first_ratio).quantize(Decimal("0.01"))
    if part_count == 2:
        return [first, total - first]
    second_ratio = Decimal(str(rng.uniform(0.25, 0.65)))
    remaining = total - first
    second = (remaining * second_ratio).quantize(Decimal("0.01"))
    return [first, second, total - first - second]


def generate_synthetic_data(
    output_dir: Path,
    platform_rows: int = 6000,
    seed: int = 20261026,
) -> GeneratedPaths:
    """Generate fictional records without reading any external source data."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    platform: list[dict[str, str]] = []
    ledger: list[dict[str, str]] = []
    truth: list[dict[str, str]] = []
    ledger_counter = 1

    for index in range(1, platform_rows + 1):
        scenario = choose_scenario(rng)
        transaction_type = rng.choices(
            SUPPORTED_TYPES, weights=[58, 17, 13, 12], k=1
        )[0]
        if scenario == "unsupported_rule":
            transaction_type = "SPECIAL_EVENT"

        transaction_date = start + timedelta(days=rng.randrange(0, 90))
        marketplace = rng.choice(MARKETPLACES)
        currency = rng.choice(CURRENCIES)
        account_id = f"ACCT-{100 + index % 37:03d}"
        order_id = f"ORD-{index:08d}"
        item_code = f"ITEM-{1000 + index:06d}"
        settlement_batch = f"BATCH-{transaction_date:%Y%m}-{1 + index % 6:02d}"

        if transaction_type == "ACCOUNT_FEE":
            order_id = ""
            item_code = ""
        if transaction_type == "ADJUSTMENT":
            order_id = ""
        if scenario == "invalid_key":
            if transaction_type in {"SALE", "REFUND"}:
                order_id = ""
            elif transaction_type == "ADJUSTMENT":
                item_code = ""
            else:
                account_id = ""

        base = Decimal(rng.randrange(800, 65000)) / Decimal("100")
        if transaction_type in {"REFUND", "ACCOUNT_FEE"}:
            base = -base
        tax = (base * Decimal("0.07")).quantize(Decimal("0.01"))
        fee = (abs(base) * Decimal("0.035")).quantize(Decimal("0.01")) * Decimal("-1")
        net = base + tax + fee

        platform_id = f"PLT-{index:08d}"
        platform.append(
            {
                "platform_record_id": platform_id,
                "account_id": account_id,
                "settlement_batch": settlement_batch,
                "transaction_type": transaction_type,
                "order_id": order_id,
                "item_code": item_code,
                "marketplace": marketplace,
                "transaction_date": transaction_date.isoformat(),
                "release_date": (transaction_date + timedelta(days=rng.randrange(0, 4))).isoformat(),
                "currency": currency,
                "gross_amount": money(base),
                "tax_amount": money(tax),
                "fee_amount": money(fee),
                "net_amount": money(net),
                "status": rng.choice(("RELEASED", "RELEASED", "PENDING")),
            }
        )
        truth.append({"platform_record_id": platform_id, "injected_scenario": scenario})

        if scenario in {"platform_only", "invalid_key", "unsupported_rule"}:
            continue

        ledger_currency = currency
        ledger_total = net
        if scenario == "amount_mismatch":
            ledger_total += rng.choice((Decimal("1.25"), Decimal("-2.40"), Decimal("4.10")))
        if scenario == "currency_mismatch":
            ledger_currency = rng.choice(tuple(c for c in CURRENCIES if c != currency))

        event_count = 2 if scenario == "ambiguous_candidate" else 1
        for event_index in range(event_count):
            event_id = f"EVT-{index:08d}-{event_index + 1}"
            event_total = ledger_total
            if event_index == 1:
                event_total += Decimal("3.00")
            parts = split_amount(event_total, rng)
            for component_index, amount in enumerate(parts):
                row = {
                    "ledger_entry_id": f"LED-{ledger_counter:09d}",
                    "event_id": event_id,
                    "account_id": account_id,
                    "settlement_batch": settlement_batch,
                    "transaction_type": transaction_type,
                    "order_id": order_id,
                    "item_code": item_code,
                    "marketplace": marketplace,
                    "posting_date": transaction_date.isoformat(),
                    "amount_category": COMPONENTS[min(component_index, len(COMPONENTS) - 1)],
                    "currency": ledger_currency,
                    "amount": money(amount),
                }
                ledger.append(row)
                ledger_counter += 1
                if rng.random() < 0.008:
                    duplicate = row.copy()
                    duplicate["ledger_entry_id"] = f"LED-{ledger_counter:09d}"
                    ledger.append(duplicate)
                    ledger_counter += 1

    # Add ledger-only events with keys that cannot exist in platform data.
    for extra in range(1, 301):
        tx_date = start + timedelta(days=rng.randrange(0, 90))
        tx_type = rng.choice(SUPPORTED_TYPES)
        order_id = f"LEDGER-ONLY-{extra:06d}"
        item_code = f"LEDGER-ITEM-{extra:06d}"
        account_id = f"LEDGER-ACCT-{extra:04d}"
        settlement = f"LEDGER-BATCH-{extra:04d}"
        if tx_type == "ACCOUNT_FEE":
            order_id = item_code = ""
        elif tx_type == "ADJUSTMENT":
            order_id = ""
        total = Decimal(rng.randrange(500, 20000)) / Decimal("100")
        if tx_type in {"REFUND", "ACCOUNT_FEE"}:
            total = -total
        ledger.append(
            {
                "ledger_entry_id": f"LED-{ledger_counter:09d}",
                "event_id": f"EVT-LEDGER-ONLY-{extra:06d}",
                "account_id": account_id,
                "settlement_batch": settlement,
                "transaction_type": tx_type,
                "order_id": order_id,
                "item_code": item_code,
                "marketplace": rng.choice(MARKETPLACES),
                "posting_date": tx_date.isoformat(),
                "amount_category": "BASE",
                "currency": rng.choice(CURRENCIES),
                "amount": money(total),
            }
        )
        ledger_counter += 1

    platform_path = output_dir / "platform_transactions.csv"
    ledger_path = output_dir / "ledger_entries.csv"
    truth_path = output_dir / "scenario_truth.csv"
    _write_csv(platform_path, platform)
    _write_csv(ledger_path, ledger)
    _write_csv(truth_path, truth)
    return GeneratedPaths(platform_path, ledger_path, truth_path)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"No rows generated for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

