from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def execute_sql_file(connection: sqlite3.Connection, path: Path) -> None:
    connection.executescript(path.read_text(encoding="utf-8"))
    connection.commit()


def load_csv_tables(
    connection: sqlite3.Connection,
    platform_path: Path,
    ledger_path: Path,
) -> tuple[int, int]:
    platform = pd.read_csv(platform_path, dtype=str, keep_default_na=False)
    ledger = pd.read_csv(ledger_path, dtype=str, keep_default_na=False)
    platform.to_sql("platform_transactions", connection, if_exists="append", index=False)
    ledger.to_sql("ledger_entries", connection, if_exists="append", index=False)
    connection.commit()
    return len(platform), len(ledger)

