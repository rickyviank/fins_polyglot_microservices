"""Unit tests for app.models — Pydantic model validation."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import CtrEntry, CtrReport, DailySummary, SarCandidate, SarReport


class TestDailySummary:
    def test_valid_construction(self):
        ds = DailySummary(
            date=date(2026, 1, 1),
            txn_count=100,
            total_volume_usd=Decimal("50000.00"),
            declined_count=3,
        )
        assert ds.date == date(2026, 1, 1)
        assert ds.txn_count == 100
        assert ds.total_volume_usd == Decimal("50000.00")
        assert ds.declined_count == 3

    def test_serialization_round_trip(self):
        ds = DailySummary(
            date=date(2026, 6, 15),
            txn_count=0,
            total_volume_usd=Decimal("0"),
            declined_count=0,
        )
        data = ds.model_dump(mode="json")
        restored = DailySummary.model_validate(data)
        assert restored == ds

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            DailySummary(date=date(2026, 1, 1), txn_count=5, total_volume_usd=Decimal("1"))  # type: ignore[call-arg]


class TestCtrEntry:
    def test_valid_entry(self):
        entry = CtrEntry(
            txn_id="txn-001",
            customer_id="c-1001",
            amount_usd=Decimal("12500.00"),
            merchant="WIRE_OUT_INTL",
            timestamp=datetime(2026, 1, 1, 9, 12, tzinfo=timezone.utc),
        )
        assert entry.txn_id == "txn-001"
        assert entry.amount_usd == Decimal("12500.00")


class TestCtrReport:
    def test_report_with_entries(self):
        entry = CtrEntry(
            txn_id="txn-001",
            customer_id="c-1001",
            amount_usd=Decimal("12500.00"),
            merchant="WIRE_OUT_INTL",
            timestamp=datetime(2026, 1, 1, 9, 12, tzinfo=timezone.utc),
        )
        report = CtrReport(date=date(2026, 1, 1), entries=[entry])
        assert len(report.entries) == 1
        assert report.entries[0].txn_id == "txn-001"

    def test_report_empty_entries(self):
        report = CtrReport(date=date(2026, 1, 1), entries=[])
        assert report.entries == []


class TestSarCandidate:
    def test_valid_candidate(self):
        sc = SarCandidate(
            customer_id="c-1001",
            score=88,
            reasons=["HIGH_AMOUNT", "FOREIGN_COUNTRY"],
            last_seen=datetime(2026, 1, 1, 23, 59, tzinfo=timezone.utc),
        )
        assert sc.score == 88
        assert len(sc.reasons) == 2


class TestSarReport:
    def test_report_with_candidates(self):
        candidate = SarCandidate(
            customer_id="c-1001",
            score=88,
            reasons=["HIGH_AMOUNT"],
            last_seen=datetime(2026, 1, 1, 23, 59, tzinfo=timezone.utc),
        )
        report = SarReport(since=date(2026, 1, 1), candidates=[candidate])
        assert len(report.candidates) == 1

    def test_report_serialization(self):
        candidate = SarCandidate(
            customer_id="c-7742",
            score=92,
            reasons=["VELOCITY", "BLACKLISTED_MERCHANT"],
            last_seen=datetime(2026, 1, 1, 22, 11, tzinfo=timezone.utc),
        )
        report = SarReport(since=date(2026, 1, 1), candidates=[candidate])
        data = report.model_dump(mode="json")
        restored = SarReport.model_validate(data)
        assert restored.candidates[0].score == 92
