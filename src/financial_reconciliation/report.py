from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .reconcile import ReconciliationOutput


COLORS = {
    "matched": "#2A9D8F",
    "amount_mismatch": "#E9C46A",
    "currency_mismatch": "#F4A261",
    "platform_only": "#E76F51",
    "ledger_only": "#C44536",
    "ambiguous_candidate": "#7B2CBF",
    "invalid_key": "#6C757D",
    "unsupported_rule": "#495057",
}


def save_outputs(
    output: ReconciliationOutput,
    reports_dir: Path,
    database_path: Path,
) -> dict[str, object]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    results = output.results.copy()
    quality = output.quality_issues.copy()
    results.to_csv(reports_dir / "reconciliation_results.csv", index=False, encoding="utf-8")
    quality.to_csv(reports_dir / "data_quality_issues.csv", index=False, encoding="utf-8")

    summary = (
        results.groupby("result_type", as_index=False)
        .agg(record_count=("result_type", "size"))
        .sort_values("record_count", ascending=False)
    )
    total = int(summary["record_count"].sum())
    summary["share"] = summary["record_count"] / total
    summary.to_csv(reports_dir / "reconciliation_summary.csv", index=False, encoding="utf-8")

    quality_summary = (
        quality.groupby("issue_type", as_index=False)
        .agg(issue_count=("issue_type", "size"))
        .sort_values("issue_count", ascending=False)
    )
    quality_summary.to_csv(reports_dir / "data_quality_summary.csv", index=False, encoding="utf-8")

    _plot_result_counts(summary, figures_dir / "reconciliation_results.png")
    _plot_result_share(summary, figures_dir / "reconciliation_share.png")
    _plot_quality(quality_summary, figures_dir / "data_quality_issues.png")

    connection = sqlite3.connect(database_path)
    results.to_sql("reconciliation_results", connection, if_exists="replace", index=False)
    quality.to_sql("data_quality_issues", connection, if_exists="replace", index=False)
    summary.to_sql("reconciliation_summary", connection, if_exists="replace", index=False)
    quality_summary.to_sql("data_quality_summary", connection, if_exists="replace", index=False)
    connection.commit()
    connection.close()

    metrics = {
        "result_rows": total,
        "result_counts": dict(zip(summary["result_type"], summary["record_count"].astype(int))),
        "quality_issue_rows": int(len(quality)),
        "quality_counts": dict(zip(quality_summary["issue_type"], quality_summary["issue_count"].astype(int))),
    }
    (reports_dir / "run_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_payload = {
        "summary": summary.to_dict("records"),
        "quality_summary": quality_summary.to_dict("records"),
        "results": results.to_dict("records"),
        "quality_issues": quality.to_dict("records"),
    }
    (reports_dir / "report_payload.json").write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metrics


def _plot_result_counts(summary: pd.DataFrame, path: Path) -> None:
    ordered = summary.sort_values("record_count")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.barh(
        ordered["result_type"], ordered["record_count"],
        color=[COLORS.get(value, "#457B9D") for value in ordered["result_type"]],
    )
    ax.set_title("Reconciliation result counts")
    ax.set_xlabel("Records")
    ax.grid(axis="x", alpha=0.2)
    for index, value in enumerate(ordered["record_count"]):
        ax.text(value + max(ordered["record_count"]) * 0.01, index, f"{int(value):,}", va="center")
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_result_share(summary: pd.DataFrame, path: Path) -> None:
    ordered = summary.sort_values("share", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.bar(
        ordered["result_type"], ordered["share"] * 100,
        color=[COLORS.get(value, "#457B9D") for value in ordered["result_type"]],
    )
    ax.set_title("Reconciliation result distribution")
    ax.set_ylabel("Share (%)")
    ax.tick_params(axis="x", rotation=35)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_quality(summary: pd.DataFrame, path: Path) -> None:
    ordered = summary.sort_values("issue_count")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.barh(ordered["issue_type"], ordered["issue_count"], color="#457B9D")
    ax.set_title("Data quality issues")
    ax.set_xlabel("Issues")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)

