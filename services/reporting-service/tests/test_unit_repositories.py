"""Unit tests for reporting-service repository (stub) functions."""
from __future__ import annotations

from datetime import date, timezone
from decimal import Decimal

from app.models import CtrReport, DailySummary, SarReport
from app.repositories import fake_ctr, fake_daily_summary, fake_sar


class TestFakeDailySummary:
    def test_returns_daily_summary_type(self):
        result = fake_daily_summary(date(2024, 6, 15))
        assert isinstance(result, DailySummary)

    def test_date_matches_input(self):
        d = date(2024, 3, 1)
        result = fake_daily_summary(d)
        assert result.date == d

    def test_has_positive_txn_count(self):
        result = fake_daily_summary(date(2024, 1, 1))
        assert result.txn_count > 0

    def test_volume_is_decimal(self):
        result = fake_daily_summary(date(2024, 1, 1))
        assert isinstance(result.total_volume_usd, Decimal)

    def test_declined_count_is_non_negative(self):
        result = fake_daily_summary(date(2024, 1, 1))
        assert result.declined_count >= 0


class TestFakeCtr:
    def test_returns_ctr_report_type(self):
        result = fake_ctr(date(2024, 6, 15))
        assert isinstance(result, CtrReport)

    def test_date_matches_input(self):
        d = date(2024, 7, 4)
        result = fake_ctr(d)
        assert result.date == d

    def test_entries_not_empty(self):
        result = fake_ctr(date(2024, 6, 15))
        assert len(result.entries) > 0

    def test_entries_have_valid_txn_ids(self):
        result = fake_ctr(date(2024, 6, 15))
        for entry in result.entries:
            assert entry.txn_id.startswith("txn-")

    def test_entries_have_utc_timestamps(self):
        result = fake_ctr(date(2024, 6, 15))
        for entry in result.entries:
            assert entry.timestamp.tzinfo == timezone.utc

    def test_entry_amounts_are_positive(self):
        result = fake_ctr(date(2024, 6, 15))
        for entry in result.entries:
            assert entry.amount_usd > 0


class TestFakeSar:
    def test_returns_sar_report_type(self):
        result = fake_sar(date(2024, 6, 1))
        assert isinstance(result, SarReport)

    def test_since_matches_input(self):
        d = date(2024, 5, 1)
        result = fake_sar(d)
        assert result.since == d

    def test_candidates_not_empty(self):
        result = fake_sar(date(2024, 6, 1))
        assert len(result.candidates) > 0

    def test_candidates_have_scores(self):
        result = fake_sar(date(2024, 6, 1))
        for c in result.candidates:
            assert 0 <= c.score <= 100

    def test_candidates_have_reasons(self):
        result = fake_sar(date(2024, 6, 1))
        for c in result.candidates:
            assert len(c.reasons) > 0

    def test_candidates_have_utc_timestamps(self):
        result = fake_sar(date(2024, 6, 1))
        for c in result.candidates:
            assert c.last_seen.tzinfo == timezone.utc
