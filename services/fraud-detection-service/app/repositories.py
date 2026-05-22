from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable

from .models import Rule, ScoreResponse


class RuleRepository:
    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def list(self) -> list[Rule]:
        return list(self._rules.values())

    def add(self, rule: Rule) -> Rule:
        self._rules[rule.id] = rule
        return rule

    def seed(self, rules: Iterable[Rule]) -> None:
        for r in rules:
            self._rules[r.id] = r


class ScoreRepository:
    def __init__(self) -> None:
        self._scores: dict[str, ScoreResponse] = {}

    def save(self, score: ScoreResponse) -> None:
        self._scores[score.txn_id] = score

    def get(self, txn_id: str) -> ScoreResponse | None:
        return self._scores.get(txn_id)


class VelocityRepository:
    """Per-customer rolling window of txn timestamps.

    Note: simple dict + list, no locking. Async handlers may interleave.
    """

    def __init__(self) -> None:
        # FIXME: needs a lock once we move off single-worker uvicorn
        self._hits: dict[str, list[datetime]] = {}

    def record(self, customer_id: str, ts: datetime) -> None:
        bucket = self._hits.setdefault(customer_id, [])
        bucket.append(ts)

    def count_within(self, customer_id: str, now: datetime, window_seconds: int) -> int:
        bucket = self._hits.get(customer_id, [])
        cutoff = now.timestamp() - window_seconds
        return sum(1 for t in bucket if t.timestamp() >= cutoff)


def new_rule_id() -> str:
    return f"rule_{uuid.uuid4().hex[:10]}"
