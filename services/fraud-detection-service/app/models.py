from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    txn_id: str = Field(..., alias="txnId")
    customer_id: str = Field(..., alias="customerId")
    amount: Decimal
    merchant: str
    country: str = Field(..., min_length=2, max_length=2)
    timestamp: datetime

    model_config = {"populate_by_name": True}


class ReasonCode(BaseModel):
    code: str
    description: str
    weight: float


class ScoreResponse(BaseModel):
    txn_id: str
    customer_id: str
    score: int
    decision: Literal["approve", "review", "decline"]
    reasons: list[ReasonCode]


class Rule(BaseModel):
    id: str
    name: str
    kind: Literal["high_amount", "foreign_country", "velocity", "blacklisted_merchant"]
    enabled: bool = True
    # `threshold` may be numeric or a string label (e.g. merchant name); kept loose on purpose.
    threshold: float | str | None = None


class RuleCreate(BaseModel):
    name: str
    kind: Literal["high_amount", "foreign_country", "velocity", "blacklisted_merchant"]
    enabled: bool = True
    threshold: float | str | None = None
