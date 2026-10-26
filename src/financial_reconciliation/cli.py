from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .database import connect, execute_sql_file, load_csv_tables
from .generate_data import generate_synthetic_data
from .reconcile import load_and_reconcile
from .report import save_outputs


def build_project(root: Path, rows: int, seed: int) -> dict[str, object]:
    data_dir = root / "data" / "generated"
    reports_dir = root / "reports"
    database_path = data_dir / "reconciliation_demo.sqlite"
    if database_path.exists():
        database_path.unlink()

    paths = generate_synthetic_data(data_dir, platform_rows=rows, seed=seed)
    connection = connect(database_path)
    execute_sql_file(connection, root / "sql" / "01_create_tables.sql")
    platform_count, ledger_count = load_csv_tables(
        connection, paths.platform_csv, paths.ledger_csv
    )
    connection.close()

    output = load_and_reconcile(paths.platform_csv, paths.ledger_csv)
    metrics = save_outputs(output, reports_dir, database_path)
    metrics.update(
        {
            "platform_rows": platform_count,
            "ledger_rows": ledger_count,
            "ledger_events": int(len(output.ledger_events)),
            "seed": seed,
        }
    )
    (reports_dir / "run_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic reconciliation demo")
    parser.add_argument("command", choices=("all", "clean"), nargs="?", default="all")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--rows", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=20261026)
    args = parser.parse_args()
    root = args.root.resolve()

    if args.command == "clean":
        for path in (root / "data" / "generated", root / "reports"):
            if path.exists():
                shutil.rmtree(path)
        print("Generated files removed.")
        return

    metrics = build_project(root, args.rows, args.seed)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

