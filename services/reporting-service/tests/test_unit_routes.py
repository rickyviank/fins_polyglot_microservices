"""Unit tests for reporting-service API routes using FastAPI TestClient."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ReportingService, get_reporting


@pytest.fixture()
def svc():
    return ReportingService(audit=None)


@pytest.fixture()
def client(svc):
    app.dependency_overrides[get_reporting] = lambda: svc
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestDailySummaryEndpoint:
    def test_valid_date(self, client):
        resp = client.get("/v1/reports/daily-summary", params={"date": "2024-06-15"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["date"] == "2024-06-15"
        assert body["txn_count"] > 0

    def test_invalid_date_returns_empty(self, client):
        resp = client.get("/v1/reports/daily-summary", params={"date": "bad-date"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["date"] == "bad-date"
        assert body["items"] == []

    def test_missing_date_param(self, client):
        resp = client.get("/v1/reports/daily-summary")
        assert resp.status_code == 422


class TestCtrEndpoint:
    def test_valid_date(self, client):
        resp = client.get("/v1/reports/ctr", params={"date": "2024-07-04"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["date"] == "2024-07-04"
        assert len(body["entries"]) > 0

    def test_invalid_date_returns_empty(self, client):
        resp = client.get("/v1/reports/ctr", params={"date": "invalid"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["entries"] == []

    def test_entry_structure(self, client):
        resp = client.get("/v1/reports/ctr", params={"date": "2024-07-04"})
        entry = resp.json()["entries"][0]
        assert "txn_id" in entry
        assert "customer_id" in entry
        assert "amount_usd" in entry
        assert "merchant" in entry
        assert "timestamp" in entry


class TestSarCandidatesEndpoint:
    def test_valid_date(self, client):
        resp = client.get("/v1/reports/sar-candidates", params={"since": "2024-06-01"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["since"] == "2024-06-01"
        assert len(body["candidates"]) > 0

    def test_invalid_date_returns_empty(self, client):
        resp = client.get("/v1/reports/sar-candidates", params={"since": "nope"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["candidates"] == []

    def test_candidate_structure(self, client):
        resp = client.get("/v1/reports/sar-candidates", params={"since": "2024-06-01"})
        cand = resp.json()["candidates"][0]
        assert "customer_id" in cand
        assert "score" in cand
        assert "reasons" in cand
        assert "last_seen" in cand


class TestExportEndpoint:
    def test_export_csv(self, client):
        client.get("/v1/reports/daily-summary", params={"date": "2024-01-01"})
        resp = client.get(
            "/v1/reports/export",
            params={"reportId": "daily-2024-01-01", "format": "csv"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"
        assert "Content-Disposition" in resp.headers

    def test_export_json(self, client):
        client.get("/v1/reports/ctr", params={"date": "2024-01-01"})
        resp = client.get(
            "/v1/reports/export",
            params={"reportId": "ctr-2024-01-01", "format": "json"},
        )
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        body = json.loads(resp.content)
        assert "entries" in body

    def test_export_regenerates_uncached_report(self, client):
        resp = client.get(
            "/v1/reports/export",
            params={"reportId": "sar-2024-03-01", "format": "json"},
        )
        assert resp.status_code == 200
        body = json.loads(resp.content)
        assert "candidates" in body

    def test_export_unknown_report_id(self, client):
        resp = client.get(
            "/v1/reports/export",
            params={"reportId": "unknown-id", "format": "json"},
        )
        assert resp.status_code == 200

    def test_export_missing_report_id(self, client):
        resp = client.get("/v1/reports/export", params={"format": "csv"})
        assert resp.status_code == 422


class TestExceptionHandlers:
    def test_not_found_error(self, client):
        from finspoly_commons import NotFoundError

        def _broken():
            svc = MagicMock()
            svc.daily_summary.side_effect = NotFoundError("not found")
            return svc

        app.dependency_overrides[get_reporting] = _broken
        resp = client.get("/v1/reports/daily-summary", params={"date": "2024-01-01"})
        assert resp.status_code == 404
        assert resp.json()["code"] == "NOT_FOUND"

    def test_validation_error_handler(self, client):
        from finspoly_commons import ValidationError as DomainValidationError

        def _broken():
            svc = MagicMock()
            svc.daily_summary.side_effect = DomainValidationError("bad input")
            return svc

        app.dependency_overrides[get_reporting] = _broken
        resp = client.get("/v1/reports/daily-summary", params={"date": "2024-01-01"})
        assert resp.status_code == 400

    def test_unauthorized_error_handler(self, client):
        from finspoly_commons import UnauthorizedError

        def _broken():
            svc = MagicMock()
            svc.daily_summary.side_effect = UnauthorizedError("denied")
            return svc

        app.dependency_overrides[get_reporting] = _broken
        resp = client.get("/v1/reports/daily-summary", params={"date": "2024-01-01"})
        assert resp.status_code == 401

    def test_domain_error_handler(self, client):
        from finspoly_commons import DomainError

        def _broken():
            svc = MagicMock()
            svc.daily_summary.side_effect = DomainError("internal")
            return svc

        app.dependency_overrides[get_reporting] = _broken
        resp = client.get("/v1/reports/daily-summary", params={"date": "2024-01-01"})
        assert resp.status_code == 500
