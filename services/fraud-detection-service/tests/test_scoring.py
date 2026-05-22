from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.models import ScoreRequest
from app.repositories import RuleRepository, ScoreRepository, VelocityRepository
from app.services import FraudScorer, seed_default_rules


def test_high_amount_triggers_rule():
    rules = RuleRepository()
    seed_default_rules(rules)
    scorer = FraudScorer(rules, ScoreRepository(), VelocityRepository(), audit=None)

    req = ScoreRequest.model_validate({
        "txnId": "t-001",
        "customerId": "c-1",
        "amount": Decimal("25000.00"),
        "merchant": "LOCAL_COFFEE",
        "country": "US",
        "timestamp": datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    })
    resp = scorer.score(req)

    codes = {r.code for r in resp.reasons}
    assert "HIGH_AMOUNT" in codes
    assert resp.score > 0
