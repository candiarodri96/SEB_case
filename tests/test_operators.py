from src.engine.operators import min_rating, in_list, equals, max_percentage_of_account


def test_rating_above_threshold():
    assert min_rating("A", "BBB-") == (True, None)


def test_rating_below_threshold():
    assert min_rating("BB", "BBB-") == (False, None)

def test_rating_exactly_at_threshold():
    assert min_rating("BBB-", "BBB-") == (True, None)

def test_rating_missing():
    result, reason = min_rating(None, "BBB-")
    assert result is None
    assert reason == "rating missing"

def test_rating_unrecognized():
    result, reason = min_rating("Baa2", "BBB-")
    assert result is None

def test_in_list():
    assert in_list("bond", ["equity", "bond", "fund"]) == (True, None)
    assert in_list("derivative", ["equity", "bond", "fund"]) == (False, None)

def test_equals():
    assert equals("LISTED", "LISTED") == (True, None)
    assert equals("DELISTED", "LISTED") == (False, None)

def test_concentration_under_limit():
    result, reason, pct = max_percentage_of_account(5000, 10, 100000)
    assert result is True
    assert pct == 5.0

def test_concentration_over_limit():
    result, reason, pct = max_percentage_of_account(15000, 10, 100000)
    assert result is False
    assert pct == 15.0

def test_concentration_zero_account():
    result, reason, pct = max_percentage_of_account(5000, 10, 0)
    assert result is None