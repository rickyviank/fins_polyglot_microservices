import pytest

from finspoly_commons import Money, usd


def test_plus_same_currency():
    assert usd(150) + usd(250) == usd(400)


def test_plus_currency_mismatch_raises():
    with pytest.raises(ValueError, match="currency mismatch"):
        usd(100) + Money(100, "EUR")
