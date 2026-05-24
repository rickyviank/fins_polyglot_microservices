"""Unit tests for app.repositories — stub data generators."""
from __future__ import annotations

from datetime import date, timezone
from decimal import Decimal

from app.repositories import fake_ctr, fake_daily_summary, fake_sar


class TestFakeDailySummary:
    def test_returns_summary_for_given_date(self):
        d = date(2026, 3, 15)
        result = fake_daily_summary(d)
        assert result.date == d
        assert result.txn_count == 12_840
        assert result.total_volume_usd == Decimal("4821553.27")
        assert result.declined_count == 47

    def test_date_is_preserved(self):
        d1 = date(2025, 1, 1)
        d2 = date(2026, 12, 31)
        assert fake_daily_summary(d1).date == d1
        assert fake_daily_summary(d2).date == d2


class TestFakeCtr:
    def test_returns_report_with_three_entries(self):
        d = date(2026, 5, 20)
        report = fake_ctr(d)
        assert report.date == d
        assert len(report.entries) == 3

    def test_entry_amounts_are_above_threshold(self):
        report = fake_ctr(date(2026, 1, 1))
        for entry in report.entries:
            assert entry.amount_usd >= Decimal("10000.00")

    def test_entry_timestamps_use_report_date(self):
        d = date(2026, 7, 4)
        report = fake_ctr(d)
        for entry in report.entries:
            assert entry.timestamp.date() == d
            assert entry.timestamp.tzinfo == timezone.utc

    def test_known_txn_ids(self):
        report = fake_ctr(date(2026, 1, 1))
        txn_ids = {e.txn_id for e in report.entries}
        assert txn_ids == {"txn-001", "txn-009", "txn-021"}


class TestFakeSar:
    def test_returns_report_with_two_candidates(self):
        d = date(2026, 1, 10)
        report = fake_sar(d)
        assert report.since == d
        assert len(report.candidates) == 2

    def test_candidate_scores_are_high(self):
        report = fake_sar(date(2026, 1, 1))
        for c in report.candidates:
            assert c.score >= 80

    def test_candidate_customer_ids(self):
        report = fake_sar(date(2026, 1, 1))
        ids = {c.customer_id for c in report.candidates}
        assert ids == {"c-1001", "c-7742"}

    def test_candidate_reasons_not_empty(self):
        report = fake_sar(date(2026, 1, 1))
        for c in report.candidates:
            assert len(c.reasons) > 0
