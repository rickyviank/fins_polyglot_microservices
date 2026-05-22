from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

from finspoly_commons import AuditClient, Money, usd

from .config import settings
from .models import ReasonCode, Rule, ScoreRequest, ScoreResponse
from .repositories import RuleRepository, ScoreRepository, VelocityRepository, new_rule_id

logger = logging.getLogger(__name__)

# Policy data — high-risk country list. Bank-internal compliance lists are typically
# pushed from a central reference-data service; inlining them here is a shortcut.
HIGH_RISK_COUNTRIES = {"IR", "KP", "SY", "CU", "RU", "BY", "VE"}
BLACKLISTED_MERCHANTS = {"DARK_BAZAAR", "QUICKCASH_OFFSHORE", "ANON_CRYPTO_LTD"}


def seed_default_rules(repo: RuleRepository) -> None:
    repo.seed(
        [
            Rule(id="rule_high_amount", name="High amount", kind="high_amount", threshold=settings.high_amount_usd),
            Rule(id="rule_foreign_country", name="Foreign / high-risk country", kind="foreign_country"),
            Rule(id="rule_velocity", name="Customer velocity", kind="velocity", threshold=settings.velocity_threshold),
            Rule(id="rule_blacklisted_merchant", name="Blacklisted merchant", kind="blacklisted_merchant"),
        ]
    )


# --- "ML" stub ----------------------------------------------------------------

# Logistic-regression-flavored weighted sum. NOT a real model.
_FEATURE_WEIGHTS = {
    "amount_norm": 0.42,
    "foreign": 0.31,
    "velocity_norm": 0.18,
    "blacklisted": 0.55,
    "night_hour": 0.07,
}


def _ml_score(features: dict[str, float]) -> float:
    s = sum(_FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in features.items())
    # squash to 0..1
    return 1.0 / (1.0 + pow(2.718281828, -s))


# --- Engine -------------------------------------------------------------------


class FraudScorer:
    def __init__(
        self,
        rule_repo: RuleRepository,
        score_repo: ScoreRepository,
        velocity_repo: VelocityRepository,
        audit: AuditClient | None = None,
    ) -> None:
        self._rules = rule_repo
        self._scores = score_repo
        self._velocity = velocity_repo
        self._audit = audit

    def add_rule(self, name: str, kind: str, threshold, enabled: bool) -> Rule:
        rule = Rule(id=new_rule_id(), name=name, kind=kind, enabled=enabled, threshold=threshold)  # type: ignore[arg-type]
        self._rules.add(rule)
        if self._audit:
            self._audit.emit(
                actor="admin",
                action="rule.create",
                resource_type="rule",
                resource_id=rule.id,
                outcome="success",
                metadata={"kind": kind, "name": name},
            )
        return rule

    def list_rules(self) -> list[Rule]:
        return self._rules.list()

    def get_score(self, txn_id: str) -> ScoreResponse | None:
        return self._scores.get(txn_id)

    def score(self, req: ScoreRequest) -> ScoreResponse:
        # Per-call info log — useful for ops dashboards.
        logger.info(
            "scoring txn=%s customer=%s amount=%s merchant=%s country=%s",
            req.txn_id, req.customer_id, req.amount, req.merchant, req.country,
        )

        reasons: list[ReasonCode] = []
        rules = [r for r in self._rules.list() if r.enabled]

        # Track velocity first so the recording is visible to the rule below.
        self._velocity.record(req.customer_id, req.timestamp)
        window_seconds = settings.velocity_window_min * 60
        vel_count = self._velocity.count_within(req.customer_id, req.timestamp, window_seconds)

        amount_money: Money = usd(int(req.amount * 100))

        for rule in rules:
            if rule.kind == "high_amount":
                # Mixing Decimal (req.amount) and float-ish threshold from the Rule model.
                if req.amount > rule.threshold:  # type: ignore[operator]
                    reasons.append(
                        ReasonCode(code="HIGH_AMOUNT", description=f"amount > {rule.threshold}", weight=0.4)
                    )
            elif rule.kind == "foreign_country":
                if req.country.upper() in HIGH_RISK_COUNTRIES:
                    reasons.append(
                        ReasonCode(code="FOREIGN_COUNTRY", description=f"country={req.country}", weight=0.3)
                    )
            elif rule.kind == "velocity":
                threshold = int(rule.threshold) if rule.threshold is not None else settings.velocity_threshold
                if vel_count >= threshold:
                    reasons.append(
                        ReasonCode(code="VELOCITY", description=f"{vel_count} txns in window", weight=0.2)
                    )
            elif rule.kind == "blacklisted_merchant":
                if req.merchant.upper() in BLACKLISTED_MERCHANTS:
                    reasons.append(
                        ReasonCode(code="BLACKLISTED_MERCHANT", description=req.merchant, weight=0.6)
                    )

        features = {
            "amount_norm": float(min(req.amount, Decimal("50000"))) / 50000.0,
            "foreign": 1.0 if req.country.upper() in HIGH_RISK_COUNTRIES else 0.0,
            "velocity_norm": min(vel_count / 10.0, 1.0),
            "blacklisted": 1.0 if req.merchant.upper() in BLACKLISTED_MERCHANTS else 0.0,
            "night_hour": 1.0 if (req.timestamp.hour < 6 or req.timestamp.hour >= 22) else 0.0,
        }
        ml_prob = _ml_score(features)

        # Combine rule reasons with ML probability.
        rule_weight = sum(r.weight for r in reasons)
        score_pct = int(min(100.0, (0.6 * ml_prob + 0.4 * min(rule_weight, 1.0)) * 100))

        if score_pct >= 80 or any(r.code == "BLACKLISTED_MERCHANT" for r in reasons):
            decision = "decline"
        elif score_pct >= 50:
            decision = "review"
        else:
            decision = "approve"

        resp = ScoreResponse(
            txn_id=req.txn_id,
            customer_id=req.customer_id,
            score=score_pct,
            decision=decision,
            reasons=reasons,
        )
        self._scores.save(resp)

        if self._audit:
            self._audit.emit(
                actor=req.customer_id,
                action="txn.score",
                resource_type="transaction",
                resource_id=req.txn_id,
                outcome="success",
                metadata={"score": score_pct, "decision": decision, "amount_str": str(amount_money)},
            )

        return resp


def _build_default_scorer() -> FraudScorer:
    rules = RuleRepository()
    seed_default_rules(rules)
    scores = ScoreRepository()
    velocity = VelocityRepository()
    audit = AuditClient(settings.audit_service_url, service=settings.service_name)
    return FraudScorer(rules, scores, velocity, audit)


_default_scorer: FraudScorer | None = None


def get_scorer() -> FraudScorer:
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = _build_default_scorer()
    return _default_scorer
