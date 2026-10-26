from financial_reconciliation.reconcile import reconcile

from conftest import frames, ledger_row, platform_row


def _types(output):
    return output.results["result_type"].tolist()


def test_one_to_many_ledger_lines_are_aggregated():
    platform, ledger = frames(
        [platform_row()],
        [ledger_row(amount="8.00"), ledger_row("LED-0002", amount="2.35", amount_category="TAX")],
    )
    output = reconcile(platform, ledger)
    assert _types(output) == ["matched"]
    assert output.results.iloc[0]["ledger_line_count"] == 2


def test_amount_mismatch_after_business_key_match():
    platform, ledger = frames([platform_row()], [ledger_row(amount="10.34")])
    output = reconcile(platform, ledger)
    assert _types(output) == ["amount_mismatch"]
    assert output.results.iloc[0]["difference_amount"] == "0.01"


def test_currency_mismatch_is_separate_from_amount():
    platform, ledger = frames([platform_row()], [ledger_row(currency="EUR")])
    assert _types(reconcile(platform, ledger)) == ["currency_mismatch"]


def test_multiple_events_with_same_key_are_ambiguous():
    platform, ledger = frames(
        [platform_row()],
        [ledger_row(), ledger_row("LED-0002", event_id="EVT-0002")],
    )
    output = reconcile(platform, ledger)
    assert _types(output) == ["ambiguous_candidate"]
    assert output.results.iloc[0]["candidate_count"] == 2


def test_bidirectional_missing_records():
    platform, ledger = frames(
        [platform_row(order_id="ORD-PLATFORM-ONLY")],
        [ledger_row(order_id="ORD-LEDGER-ONLY")],
    )
    assert set(_types(reconcile(platform, ledger))) == {"platform_only", "ledger_only"}


def test_missing_required_business_key_is_invalid():
    platform, ledger = frames([platform_row(order_id="")], [ledger_row()])
    output = reconcile(platform, ledger)
    assert "invalid_key" in _types(output)


def test_unsupported_transaction_type_is_not_force_matched():
    platform, ledger = frames(
        [platform_row(transaction_type="SPECIAL_EVENT")],
        [ledger_row(transaction_type="SPECIAL_EVENT")],
    )
    assert _types(reconcile(platform, ledger)) == ["unsupported_rule"]


def test_exact_duplicate_ledger_row_is_flagged_and_excluded():
    platform, ledger = frames(
        [platform_row()],
        [ledger_row(), ledger_row("LED-0002")],
    )
    output = reconcile(platform, ledger)
    assert _types(output) == ["matched"]
    assert "exact_duplicate_ledger_row" in set(output.quality_issues["issue_type"])


def test_result_count_conservation():
    platform, ledger = frames(
        [platform_row(), platform_row(platform_record_id="PLT-0002", order_id="ORD-0002")],
        [ledger_row(), ledger_row("LED-0002", event_id="EVT-0002", order_id="ORD-LEDGER-ONLY")],
    )
    output = reconcile(platform, ledger)
    # Two platform decisions plus one unconsumed ledger event.
    assert len(output.results) == 3

