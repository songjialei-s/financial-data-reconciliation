import pandas as pd

from financial_reconciliation.generate_data import generate_synthetic_data
from financial_reconciliation.reconcile import load_and_reconcile


def test_generated_pipeline_contains_required_scenarios(tmp_path):
    paths = generate_synthetic_data(tmp_path, platform_rows=1000, seed=12345)
    platform = pd.read_csv(paths.platform_csv)
    ledger = pd.read_csv(paths.ledger_csv)
    assert len(platform) == 1000
    assert len(ledger) > 1000

    output = load_and_reconcile(paths.platform_csv, paths.ledger_csv)
    required = {
        "matched", "amount_mismatch", "currency_mismatch", "platform_only",
        "ledger_only", "ambiguous_candidate", "invalid_key", "unsupported_rule",
    }
    assert required.issubset(set(output.results["result_type"]))

