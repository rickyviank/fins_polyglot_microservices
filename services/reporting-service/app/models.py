from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class DailySummary(BaseModel):
    date: date
    txn_count: int
    total_volume_usd: Decimal
    declined_count: int


class CtrEntry(BaseModel):
    txn_id: str
    customer_id: str
    amount_usd: Decimal
    merchant: str
    timestamp: datetime


class CtrReport(BaseModel):
    date: date
    entries: list[CtrEntry]


class SarCandidate(BaseModel):
    customer_id: str
    score: int
    reasons: list[str]
    last_seen: datetime


class SarReport(BaseModel):
    since: date
    candidates: list[SarCandidate]


ReportFormat = Literal["csv", "json"]
