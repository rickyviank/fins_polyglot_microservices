"""Unit tests for reporting-service Pydantic models."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import (
    CtrEntry,
    CtrReport,
    DailySummary,
    ReportFormat,
    SarCandidate,
    SarReport,
)


class TestDailySummary:
    def test_valid_construction(self):
        summary = DailySummary(
            date=date(2024, 6, 15),
            txn_count=100,
            total_volume_usd=Decimal("50000.00"),
            declined_count=3,
        )
        assert summary.date == date(2024, 6, 15)
        assert summary.txn_count == 100
        assert summary.total_volume_usd == Decimal("50000.00")
        assert summary.declined_count == 3

    def test_serialisation_roundtrip(self):
        summary = DailySummary(
            date=date(2024, 1, 1),
            txn_count=0,
            total_volume_usd=Decimal("0"),
            declined_count=0,
        )
        data = summary.model_dump(mode="json")
        restored = DailySummary.model_validate(data)
        assert restored == summary

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            DailySummary(date=date(2024, 1, 1), txn_count=1)  # type: ignore[call-arg]


class TestCtrEntry:
    def test_valid_construction(self):
        entry = CtrEntry(
            txn_id="txn-001",
            customer_id="c-1001",
            amount_usd=Decimal("12500.00"),
            merchant="WIRE_OUT_INTL",
            timestamp=datetime(2024, 6, 15, 9, 12, tzinfo=timezone.utc),
        )
        assert entry.txn_id == "txn-001"
        assert entry.customer_id == "c-1001"
        assert entry.amount_usd == Decimal("12500.00")
        assert entry.merchant == "WIRE_OUT_INTL"

    def test_missing_txn_id_raises(self):
        with pytest.raises(ValidationError):
            CtrEntry(
                customer_id="c-1001",
                amount_usd=Decimal("100"),
                merchant="M",
                timestamp=datetime.now(timezone.utc),
            )  # type: ignore[call-arg]


class TestCtrReport:
    def test_valid_with_entries(self):
        report = CtrReport(
            date=date(2024, 6, 15),
            entries=[
                CtrEntry(
                    txn_id="t1",
                    customer_id="c1",
                    amount_usd=Decimal("10000"),
                    merchant="M1",
                    timestamp=datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        assert len(report.entries) == 1
        assert report.date == date(2024, 6, 15)

    def test_empty_entries(self):
        report = CtrReport(date=date(2024, 1, 1), entries=[])
        assert report.entries == []


class TestSarCandidate:
    def test_valid_construction(self):
        candidate = SarCandidate(
            customer_id="c-1001",
            score=88,
            reasons=["HIGH_AMOUNT", "FOREIGN_COUNTRY"],
            last_seen=datetime(2024, 6, 15, 23, 59, tzinfo=timezone.utc),
        )
        assert candidate.score == 88
        assert len(candidate.reasons) == 2

    def test_empty_reasons_list(self):
        candidate = SarCandidate(
            customer_id="c-1",
            score=50,
            reasons=[],
            last_seen=datetime.now(timezone.utc),
        )
        assert candidate.reasons == []


class TestSarReport:
    def test_valid_construction(self):
        report = SarReport(
            since=date(2024, 6, 1),
            candidates=[
                SarCandidate(
                    customer_id="c-1",
                    score=90,
                    reasons=["VELOCITY"],
                    last_seen=datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        assert report.since == date(2024, 6, 1)
        assert len(report.candidates) == 1

    def test_empty_candidates(self):
        report = SarReport(since=date(2024, 1, 1), candidates=[])
        assert report.candidates == []


class TestReportFormat:
    def test_csv_is_valid(self):
        fmt: ReportFormat = "csv"
        assert fmt == "csv"

    def test_json_is_valid(self):
        fmt: ReportFormat = "json"
        assert fmt == "json"
