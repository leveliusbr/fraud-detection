import pandas as pd
import pytest
from features import build_model_frame


def _accounts(*rows):
    return pd.DataFrame(rows)


def _transactions(*rows):
    return pd.DataFrame(rows)


def _single_pair(amount_usd=100, failed_logins_24h=0, prior_chargebacks=0):
    txns = _transactions({"transaction_id": 1, "account_id": 1, "amount_usd": amount_usd, "failed_logins_24h": failed_logins_24h})
    accts = _accounts({"account_id": 1, "prior_chargebacks": prior_chargebacks})
    return build_model_frame(txns, accts)


# --- merge ---

def test_account_fields_present_after_merge():
    df = _single_pair(prior_chargebacks=2)
    assert "prior_chargebacks" in df.columns
    assert df.loc[0, "prior_chargebacks"] == 2


def test_transaction_with_no_matching_account_is_kept():
    txns = _transactions({"transaction_id": 1, "account_id": 99, "amount_usd": 100, "failed_logins_24h": 0})
    accts = _accounts({"account_id": 1, "prior_chargebacks": 0})
    df = build_model_frame(txns, accts)
    assert len(df) == 1


# --- is_large_amount ---

def test_amount_below_1000_is_not_large():
    df = _single_pair(amount_usd=999)
    assert df.loc[0, "is_large_amount"] == 0


def test_amount_at_1000_is_large():
    df = _single_pair(amount_usd=1000)
    assert df.loc[0, "is_large_amount"] == 1


def test_amount_above_1000_is_large():
    df = _single_pair(amount_usd=5000)
    assert df.loc[0, "is_large_amount"] == 1


# --- login_pressure ---

def test_zero_failed_logins_is_none():
    df = _single_pair(failed_logins_24h=0)
    assert str(df.loc[0, "login_pressure"]) == "none"


def test_one_or_two_failed_logins_is_low():
    for n in (1, 2):
        df = _single_pair(failed_logins_24h=n)
        assert str(df.loc[0, "login_pressure"]) == "low", f"expected low for failed_logins={n}"


def test_three_or_more_failed_logins_is_high():
    for n in (3, 10):
        df = _single_pair(failed_logins_24h=n)
        assert str(df.loc[0, "login_pressure"]) == "high", f"expected high for failed_logins={n}"
