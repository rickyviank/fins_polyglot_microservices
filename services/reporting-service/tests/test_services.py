"""Unit tests for app.services — ReportingService, _json_bytes, _csv_bytes."""
from __future__ import annotations

import csv
import io
import json
import os
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services import (
    ReportingService,
    _REPORT_CACHE,
    _csv_bytes,
    _json_bytes,
    get_reporting,
)


class TestReportingServiceDailySummary:
    def test_valid_date_returns_summary(self, svc: ReportingService):
        result = svc.daily_summary("2026-03-15")
        assert result is not None
        assert result.date == date(2026, 3, 15)
        assert result.txn_count == 12_840

    def test_invalid_date_returns_none(self, svc: ReportingService):
        assert svc.daily_summary("not-a-date") is None

    def test_empty_string_returns_none(self, svc: ReportingService):
        assert svc.daily_summary("") is None

    def test_wrong_format_returns_none(self, svc: ReportingService):
        assert svc.daily_summary("15/03/2026") is None

    def test_caches_result(self, svc: ReportingService):
        svc.daily_summary("2026-01-01")
        assert "daily-2026-01-01" in _REPORT_CACHE

    def test_cached_data_matches_model(self, svc: ReportingService):
        result = svc.daily_summary("2026-06-15")
        assert result is not None
        cached = _REPORT_CACHE["daily-2026-06-15"]
        assert cached["txn_count"] == result.txn_count


class TestReportingServiceCtr:
    def test_valid_date_returns_ctr(self, svc: ReportingService):
        result = svc.ctr("2026-05-20")
        assert result is not None
        assert len(result.entries) == 3

    def test_invalid_date_returns_none(self, svc: ReportingService):
        assert svc.ctr("bad") is None

    def test_caches_result(self, svc: ReportingService):
        svc.ctr("2026-02-28")
        assert "ctr-2026-02-28" in _REPORT_CACHE


class TestReportingServiceSar:
    def test_valid_date_returns_sar(self, svc: ReportingService):
        result = svc.sar_candidates("2026-01-10")
        assert result is not None
        assert len(result.candidates) == 2

    def test_invalid_date_returns_none(self, svc: ReportingService):
        assert svc.sar_candidates("invalid") is None

    def test_caches_result(self, svc: ReportingService):
        svc.sar_candidates("2026-04-01")
        assert "sar-2026-04-01" in _REPORT_CACHE


class TestReportingServiceExport:
    def test_export_json_from_cache(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.daily_summary("2026-01-01")
            body, media, disposition = svc.export("daily-2026-01-01", "json")
            assert media == "application/json"
            assert b"txn_count" in body
            parsed = json.loads(body)
            assert parsed["txn_count"] == 12_840

    def test_export_csv_from_cache(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.daily_summary("2026-01-01")
            body, media, disposition = svc.export("daily-2026-01-01", "csv")
            assert media == "text/csv"
            reader = csv.reader(io.StringIO(body.decode("utf-8")))
            rows = list(reader)
            assert len(rows) == 2  # header + data

    def test_export_csv_ctr_entries(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.ctr("2026-01-01")
            body, media, _ = svc.export("ctr-2026-01-01", "csv")
            assert media == "text/csv"
            reader = csv.reader(io.StringIO(body.decode("utf-8")))
            rows = list(reader)
            assert len(rows) == 4  # header + 3 entries

    def test_export_creates_file(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.daily_summary("2026-01-01")
            svc.export("daily-2026-01-01", "json")
            assert (tmp_path / "daily-2026-01-01.json").exists()

    def test_export_content_disposition(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.daily_summary("2026-01-01")
            _, _, disposition = svc.export("daily-2026-01-01", "json")
            assert 'filename="daily-2026-01-01.json"' in disposition

    def test_export_unknown_report_id_returns_empty(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            body, media, _ = svc.export("unknown-report", "json")
            parsed = json.loads(body)
            assert "id" in parsed
            assert parsed["items"] == []

    def test_export_regenerates_known_prefix(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            body, _, _ = svc.export("daily-2026-03-15", "json")
            parsed = json.loads(body)
            assert parsed["txn_count"] == 12_840

    def test_export_regenerates_ctr_prefix(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            body, _, _ = svc.export("ctr-2026-03-15", "json")
            parsed = json.loads(body)
            assert len(parsed["entries"]) == 3

    def test_export_regenerates_sar_prefix(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            body, _, _ = svc.export("sar-2026-03-15", "json")
            parsed = json.loads(body)
            assert len(parsed["candidates"]) == 2

    def test_export_with_audit_emits(self, tmp_path):
        mock_audit = MagicMock()
        svc = ReportingService(audit=mock_audit)
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.daily_summary("2026-01-01")
            svc.export("daily-2026-01-01", "csv")
            mock_audit.emit.assert_called_once_with(
                actor="ops",
                action="report.export",
                resource_type="report",
                resource_id="daily-2026-01-01",
                outcome="success",
                metadata={"format": "csv"},
            )

    def test_export_without_audit_does_not_raise(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            svc.daily_summary("2026-01-01")
            body, _, _ = svc.export("daily-2026-01-01", "json")
            assert len(body) > 0

    def test_export_zip_failure_is_swallowed(self, svc: ReportingService, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            with patch("subprocess.run", side_effect=OSError("zip not found")):
                svc.daily_summary("2026-01-01")
                body, _, _ = svc.export("daily-2026-01-01", "json")
                assert len(body) > 0


class TestRegenerate:
    def test_regenerate_invalid_daily_date(self, svc: ReportingService):
        result = svc._regenerate("daily-invalid")
        assert result is None

    def test_regenerate_invalid_ctr_date(self, svc: ReportingService):
        result = svc._regenerate("ctr-invalid")
        assert result is None

    def test_regenerate_invalid_sar_date(self, svc: ReportingService):
        result = svc._regenerate("sar-invalid")
        assert result is None

    def test_regenerate_unknown_prefix(self, svc: ReportingService):
        result = svc._regenerate("xyz-2026-01-01")
        assert result is None


class TestJsonBytes:
    def test_round_trip(self):
        data = {"key": "value", "number": 42}
        result = _json_bytes(data)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_handles_decimal_via_default_str(self):
        data = {"amount": Decimal("123.45")}
        result = _json_bytes(data)
        parsed = json.loads(result)
        assert parsed["amount"] == "123.45"

    def test_handles_date_via_default_str(self):
        data = {"d": date(2026, 1, 1)}
        result = _json_bytes(data)
        parsed = json.loads(result)
        assert parsed["d"] == "2026-01-01"


class TestCsvBytes:
    def test_flat_dict_produces_two_rows(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = _csv_bytes(data)
        lines = result.decode("utf-8").strip().split("\n")
        assert len(lines) == 2

    def test_entries_list(self):
        data = {
            "entries": [
                {"txn_id": "t1", "amount": "100"},
                {"txn_id": "t2", "amount": "200"},
            ]
        }
        result = _csv_bytes(data)
        reader = csv.reader(io.StringIO(result.decode("utf-8")))
        rows = list(reader)
        assert rows[0] == ["txn_id", "amount"]
        assert len(rows) == 3  # header + 2 rows

    def test_candidates_list(self):
        data = {
            "candidates": [
                {"customer_id": "c-1", "score": 88},
            ]
        }
        result = _csv_bytes(data)
        reader = csv.reader(io.StringIO(result.decode("utf-8")))
        rows = list(reader)
        assert rows[0] == ["customer_id", "score"]

    def test_empty_entries(self):
        data = {"entries": []}
        result = _csv_bytes(data)
        reader = csv.reader(io.StringIO(result.decode("utf-8")))
        rows = list(reader)
        assert len(rows) == 2  # falls through to single-row


class TestGetReporting:
    def test_returns_singleton(self):
        import app.services as mod

        mod._default = None
        svc1 = get_reporting()
        svc2 = get_reporting()
        assert svc1 is svc2
        mod._default = None  # cleanup
