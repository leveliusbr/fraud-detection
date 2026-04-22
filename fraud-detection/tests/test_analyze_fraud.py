import pandas as pd
from analyze_fraud import load_inputs, score_transactions, summarize_results

# Transaction IDs confirmed as fraud in chargebacks.csv.
CONFIRMED_FRAUD_IDS = {50003, 50006, 50008, 50011, 50013, 50014, 50015, 50019}


# --- summarize_results unit tests ---

def _scored(*rows):
    return pd.DataFrame(rows)


def _chargebacks(*ids):
    return pd.DataFrame({"transaction_id": list(ids)})


def test_chargeback_rate_is_fraction_of_tier():
    scored = _scored(
        {"transaction_id": 1, "risk_label": "high", "amount_usd": 500},
        {"transaction_id": 2, "risk_label": "high", "amount_usd": 500},
        {"transaction_id": 3, "risk_label": "low",  "amount_usd": 100},
    )
    summary = summarize_results(scored, _chargebacks(1)).set_index("risk_label")
    assert summary.loc["high", "chargeback_rate"] == 0.5
    assert summary.loc["low",  "chargeback_rate"] == 0.0


def test_all_chargebacks_gives_rate_of_one():
    scored = _scored(
        {"transaction_id": 1, "risk_label": "high", "amount_usd": 500},
        {"transaction_id": 2, "risk_label": "high", "amount_usd": 500},
    )
    summary = summarize_results(scored, _chargebacks(1, 2)).set_index("risk_label")
    assert summary.loc["high", "chargeback_rate"] == 1.0


def test_no_chargebacks_gives_rate_of_zero():
    scored = _scored(
        {"transaction_id": 1, "risk_label": "high", "amount_usd": 500},
        {"transaction_id": 2, "risk_label": "low",  "amount_usd": 100},
    )
    summary = summarize_results(scored, _chargebacks())
    assert (summary["chargeback_rate"] == 0).all()


def test_transaction_count_per_label_is_correct():
    scored = _scored(
        {"transaction_id": 1, "risk_label": "high",   "amount_usd": 500},
        {"transaction_id": 2, "risk_label": "medium",  "amount_usd": 300},
        {"transaction_id": 3, "risk_label": "medium",  "amount_usd": 200},
        {"transaction_id": 4, "risk_label": "low",     "amount_usd": 50},
    )
    summary = summarize_results(scored, _chargebacks()).set_index("risk_label")
    assert summary.loc["high",   "transactions"] == 1
    assert summary.loc["medium", "transactions"] == 2
    assert summary.loc["low",    "transactions"] == 1


# --- integration: real data ---

def test_no_confirmed_fraud_labeled_low():
    accounts, transactions, chargebacks = load_inputs()
    scored = score_transactions(transactions, accounts)
    fraud_rows = scored[scored["transaction_id"].isin(CONFIRMED_FRAUD_IDS)]
    low_fraud = fraud_rows[fraud_rows["risk_label"] == "low"]
    assert low_fraud.empty, (
        f"Confirmed fraud transactions scored 'low':\n"
        f"{low_fraud[['transaction_id', 'risk_score', 'risk_label']].to_string()}"
    )


def test_high_risk_tier_has_highest_chargeback_rate():
    accounts, transactions, chargebacks = load_inputs()
    scored = score_transactions(transactions, accounts)
    summary = summarize_results(scored, chargebacks).set_index("risk_label")
    assert summary.loc["high", "chargeback_rate"] > summary.loc["medium", "chargeback_rate"]
    assert summary.loc["medium", "chargeback_rate"] > summary.loc["low", "chargeback_rate"]


def test_low_risk_tier_has_zero_chargeback_rate():
    accounts, transactions, chargebacks = load_inputs()
    scored = score_transactions(transactions, accounts)
    summary = summarize_results(scored, chargebacks).set_index("risk_label")
    assert summary.loc["low", "chargeback_rate"] == 0.0
