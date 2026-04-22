from risk_rules import label_risk, score_transaction


def _base_tx(**overrides):
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 100,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    tx.update(overrides)
    return tx


# --- label_risk ---

def test_label_risk_low_boundary():
    assert label_risk(0) == "low"
    assert label_risk(29) == "low"


def test_label_risk_medium_boundary():
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"


def test_label_risk_high_boundary():
    assert label_risk(60) == "high"
    assert label_risk(100) == "high"


# --- score_transaction: clean baseline ---

def test_clean_transaction_scores_zero():
    assert score_transaction(_base_tx()) == 0


def test_clean_transaction_labels_low():
    assert label_risk(score_transaction(_base_tx())) == "low"


# --- device_risk_score ---

def test_high_device_risk_adds_25():
    assert score_transaction(_base_tx(device_risk_score=70)) == 25
    assert score_transaction(_base_tx(device_risk_score=99)) == 25


def test_mid_device_risk_adds_10():
    assert score_transaction(_base_tx(device_risk_score=40)) == 10
    assert score_transaction(_base_tx(device_risk_score=69)) == 10


def test_low_device_risk_adds_nothing():
    assert score_transaction(_base_tx(device_risk_score=39)) == 0


# --- is_international ---

def test_international_adds_15():
    assert score_transaction(_base_tx(is_international=1)) == 15


def test_domestic_adds_nothing():
    assert score_transaction(_base_tx(is_international=0)) == 0


# --- amount_usd ---

def test_large_amount_adds_25():
    assert score_transaction(_base_tx(amount_usd=1000)) == 25
    assert score_transaction(_base_tx(amount_usd=5000)) == 25


def test_mid_amount_adds_10():
    assert score_transaction(_base_tx(amount_usd=500)) == 10
    assert score_transaction(_base_tx(amount_usd=999)) == 10


def test_small_amount_adds_nothing():
    assert score_transaction(_base_tx(amount_usd=499)) == 0


# --- velocity_24h ---

def test_high_velocity_adds_20():
    assert score_transaction(_base_tx(velocity_24h=6)) == 20
    assert score_transaction(_base_tx(velocity_24h=20)) == 20


def test_mid_velocity_adds_5():
    assert score_transaction(_base_tx(velocity_24h=3)) == 5
    assert score_transaction(_base_tx(velocity_24h=5)) == 5


def test_low_velocity_adds_nothing():
    assert score_transaction(_base_tx(velocity_24h=2)) == 0


# --- failed_logins_24h ---

def test_high_failed_logins_adds_20():
    assert score_transaction(_base_tx(failed_logins_24h=5)) == 20
    assert score_transaction(_base_tx(failed_logins_24h=10)) == 20


def test_mid_failed_logins_adds_10():
    assert score_transaction(_base_tx(failed_logins_24h=2)) == 10
    assert score_transaction(_base_tx(failed_logins_24h=4)) == 10


def test_no_failed_logins_adds_nothing():
    assert score_transaction(_base_tx(failed_logins_24h=0)) == 0


# --- prior_chargebacks ---

def test_two_plus_chargebacks_add_20():
    assert score_transaction(_base_tx(prior_chargebacks=2)) == 20
    assert score_transaction(_base_tx(prior_chargebacks=5)) == 20


def test_one_chargeback_adds_5():
    assert score_transaction(_base_tx(prior_chargebacks=1)) == 5


def test_no_chargebacks_adds_nothing():
    assert score_transaction(_base_tx(prior_chargebacks=0)) == 0


# --- score clamping ---

def test_score_capped_at_100():
    tx = _base_tx(
        device_risk_score=75,
        is_international=1,
        amount_usd=1200,
        velocity_24h=8,
        failed_logins_24h=5,
        prior_chargebacks=2,
    )
    assert score_transaction(tx) == 100


def test_score_floor_is_zero():
    assert score_transaction(_base_tx()) >= 0
