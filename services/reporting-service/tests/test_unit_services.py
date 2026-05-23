"""Unit tests for ReportingService and helper functions."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models import CtrReport, DailySummary, SarReport
from app.services import (
    ReportingService,
    _csv_bytes,
    _json_bytes,
    _REPORT_CACHE,
    get_reporting,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure the report cache is clean before and after each test."""
    _REPORT_CACHE.clear()
    yield
    _REPORT_CACHE.clear()


@pytest.fixture()
def _clear_singleton():
    """Reset the module-level singleton so get_reporting() creates fresh."""
    import app.services as svc_mod
    svc_mod._default = None
    yield
    svc_mod._default = None


@pytest.fixture()
def tmp_reports_dir(tmp_path):
    """Patch settings.reports_dir to a temp directory."""
    with patch("app.services.settings") as mock_settings:
        mock_settings.reports_dir = str(tmp_path)
        mock_settings.audit_service_url = "http://localhost:8089"
        mock_settings.service_name = "reporting-service"
        yield tmp_path


class TestDailySummary:
    def test_valid_date_returns_daily_summary(self):
        svc = ReportingService()
        result = svc.daily_summary("2024-06-15")
        assert isinstance(result, DailySummary)
        assert result.date == date(2024, 6, 15)

    def test_result_cached(self):
        svc = ReportingService()
        svc.daily_summary("2024-06-15")
        assert "daily-2024-06-15" in _REPORT_CACHE

    def test_invalid_date_returns_none(self):
        svc = ReportingService()
        result = svc.daily_summary("not-a-date")
        assert result is None

    def test_malformed_date_format_returns_none(self):
        svc = ReportingService()
        result = svc.daily_summary("15/06/2024")
        assert result is None


class TestCtr:
    def test_valid_date_returns_ctr_report(self):
        svc = ReportingService()
        result = svc.ctr("2024-07-04")
        assert isinstance(result, CtrReport)
        assert result.date == date(2024, 7, 4)

    def test_result_cached(self):
        svc = ReportingService()
        svc.ctr("2024-07-04")
        assert "ctr-2024-07-04" in _REPORT_CACHE

    def test_invalid_date_returns_none(self):
        svc = ReportingService()
        result = svc.ctr("bad")
        assert result is None


class TestSarCandidates:
    def test_valid_date_returns_sar_report(self):
        svc = ReportingService()
        result = svc.sar_candidates("2024-05-01")
        assert isinstance(result, SarReport)
        assert result.since == date(2024, 5, 1)

    def test_result_cached(self):
        svc = ReportingService()
        svc.sar_candidates("2024-05-01")
        assert "sar-2024-05-01" in _REPORT_CACHE

    def test_invalid_date_returns_none(self):
        svc = ReportingService()
        result = svc.sar_candidates("xyz")
        assert result is None


class TestExport:
    def test_export_json_from_cache(self, tmp_reports_dir):
        svc = ReportingService()
        svc.daily_summary("2024-06-15")
        body, media, disp = svc.export("daily-2024-06-15", "json")
        assert media == "application/json"
        assert b"2024-06-15" in body
        parsed = json.loads(body)
        assert "date" in parsed

    def test_export_csv_from_cache(self, tmp_reports_dir):
        svc = ReportingService()
        svc.ctr("2024-06-15")
        body, media, disp = svc.export("ctr-2024-06-15", "csv")
        assert media == "text/csv"
        assert b"txn_id" in body

    def test_export_content_disposition(self, tmp_reports_dir):
        svc = ReportingService()
        svc.daily_summary("2024-01-01")
        _, _, disp = svc.export("daily-2024-01-01", "json")
        assert 'filename="daily-2024-01-01.json"' in disp

    def test_export_regenerates_on_cache_miss(self, tmp_reports_dir):
        svc = ReportingService()
        body, media, _ = svc.export("daily-2024-03-01", "json")
        assert media == "application/json"
        parsed = json.loads(body)
        assert parsed.get("date") == "2024-03-01"

    def test_export_unknown_prefix_returns_fallback(self, tmp_reports_dir):
        svc = ReportingService()
        body, media, _ = svc.export("unknown-id", "json")
        assert media == "application/json"
        parsed = json.loads(body)
        assert parsed["id"] == "unknown-id"

    def test_export_writes_file_to_reports_dir(self, tmp_reports_dir):
        svc = ReportingService()
        svc.daily_summary("2024-01-01")
        svc.export("daily-2024-01-01", "csv")
        assert os.path.exists(os.path.join(str(tmp_reports_dir), "daily-2024-01-01.csv"))

    def test_export_emits_audit_event(self, tmp_reports_dir):
        audit = MagicMock()
        svc = ReportingService(audit=audit)
        svc.daily_summary("2024-01-01")
        svc.export("daily-2024-01-01", "json")
        audit.emit.assert_called_once_with(
            actor="ops",
            action="report.export",
            resource_type="report",
            resource_id="daily-2024-01-01",
            outcome="success",
            metadata={"format": "json"},
        )

    def test_export_no_audit_when_client_is_none(self, tmp_reports_dir):
        svc = ReportingService(audit=None)
        svc.daily_summary("2024-01-01")
        body, _, _ = svc.export("daily-2024-01-01", "json")
        assert len(body) > 0

    def test_export_zip_failure_is_tolerated(self, tmp_reports_dir):
        svc = ReportingService()
        svc.daily_summary("2024-01-01")
        with patch("app.services.subprocess.run", side_effect=OSError("zip not found")):
            body, _, _ = svc.export("daily-2024-01-01", "csv")
        assert len(body) > 0


class TestRegenerate:
    def test_regenerate_daily(self):
        svc = ReportingService()
        result = svc._regenerate("daily-2024-06-15")
        assert result is not None
        assert result["date"] == "2024-06-15"

    def test_regenerate_ctr(self):
        svc = ReportingService()
        result = svc._regenerate("ctr-2024-06-15")
        assert result is not None
        assert "entries" in result

    def test_regenerate_sar(self):
        svc = ReportingService()
        result = svc._regenerate("sar-2024-06-15")
        assert result is not None
        assert "candidates" in result

    def test_regenerate_unknown_prefix_returns_none(self):
        svc = ReportingService()
        result = svc._regenerate("unknown-2024-06-15")
        assert result is None

    def test_regenerate_bad_date_returns_none(self):
        svc = ReportingService()
        result = svc._regenerate("daily-not-a-date")
        assert result is None


class TestJsonBytes:
    def test_produces_valid_json(self):
        data = {"key": "value", "count": 42}
        result = _json_bytes(data)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["count"] == 42

    def test_handles_date_serialisation(self):
        data = {"date": date(2024, 6, 15)}
        result = _json_bytes(data)
        parsed = json.loads(result)
        assert "2024-06-15" in parsed["date"]

    def test_returns_bytes(self):
        result = _json_bytes({"a": 1})
        assert isinstance(result, bytes)

    def test_utf8_encoded(self):
        data = {"name": "café"}
        result = _json_bytes(data)
        decoded = result.decode("utf-8")
        assert "caf" in decoded
        assert "name" in decoded


class TestCsvBytes:
    def test_list_entries_produces_header_and_rows(self):
        data = {
            "entries": [
                {"txn_id": "t1", "amount": "100"},
                {"txn_id": "t2", "amount": "200"},
            ]
        }
        result = _csv_bytes(data)
        lines = result.decode("utf-8").strip().split("\n")
        assert len(lines) == 3
        assert "txn_id" in lines[0]

    def test_list_candidates_key(self):
        data = {
            "candidates": [
                {"customer_id": "c1", "score": "90"},
            ]
        }
        result = _csv_bytes(data)
        reader = csv.reader(io.StringIO(result.decode("utf-8")))
        headers = next(reader)
        assert "customer_id" in headers

    def test_single_row_fallback(self):
        data = {"date": "2024-06-15", "txn_count": 100}
        result = _csv_bytes(data)
        lines = result.decode("utf-8").strip().split("\n")
        assert len(lines) == 2
        assert "date" in lines[0]
        assert "100" in lines[1]

    def test_empty_entries_uses_single_row(self):
        data = {"entries": [], "date": "2024-06-15"}
        result = _csv_bytes(data)
        lines = result.decode("utf-8").strip().split("\n")
        assert "date" in lines[0]

    def test_returns_bytes(self):
        result = _csv_bytes({"a": 1})
        assert isinstance(result, bytes)


class TestGetReporting:
    def test_returns_reporting_service(self, _clear_singleton):
        svc = get_reporting()
        assert isinstance(svc, ReportingService)

    def test_returns_singleton(self, _clear_singleton):
        svc1 = get_reporting()
        svc2 = get_reporting()
        assert svc1 is svc2
