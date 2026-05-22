from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from .models import CtrEntry, CtrReport, DailySummary, SarCandidate, SarReport


# Stub data store. In real life these come from txn-service + fraud-detection-service.
def fake_daily_summary(d: date) -> DailySummary:
    return DailySummary(
        date=d,
        txn_count=12_840,
        total_volume_usd=Decimal("4821553.27"),
        declined_count=47,
    )


def fake_ctr(d: date) -> CtrReport:
    return CtrReport(
        date=d,
        entries=[
            CtrEntry(
                txn_id="txn-001",
                customer_id="c-1001",
                amount_usd=Decimal("12500.00"),
                merchant="WIRE_OUT_INTL",
                timestamp=datetime(d.year, d.month, d.day, 9, 12, tzinfo=timezone.utc),
            ),
            CtrEntry(
                txn_id="txn-009",
                customer_id="c-2210",
                amount_usd=Decimal("15400.55"),
                merchant="LUXURY_AUTO_INC",
                timestamp=datetime(d.year, d.month, d.day, 14, 30, tzinfo=timezone.utc),
            ),
            CtrEntry(
                txn_id="txn-021",
                customer_id="c-3380",
                amount_usd=Decimal("10250.00"),
                merchant="=CMD_FORMULA_TEST",  # comes from upstream merchant names
                timestamp=datetime(d.year, d.month, d.day, 17, 5, tzinfo=timezone.utc),
            ),
        ],
    )


def fake_sar(since: date) -> SarReport:
    return SarReport(
        since=since,
        candidates=[
            SarCandidate(
                customer_id="c-1001",
                score=88,
                reasons=["HIGH_AMOUNT", "FOREIGN_COUNTRY"],
                last_seen=datetime(since.year, since.month, since.day, 23, 59, tzinfo=timezone.utc),
            ),
            SarCandidate(
                customer_id="c-7742",
                score=92,
                reasons=["VELOCITY", "BLACKLISTED_MERCHANT"],
                last_seen=datetime(since.year, since.month, since.day, 22, 11, tzinfo=timezone.utc),
            ),
        ],
    )
