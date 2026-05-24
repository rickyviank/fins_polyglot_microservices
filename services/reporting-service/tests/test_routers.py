"""Unit tests for app.routers.reports — FastAPI endpoint integration."""
from __future__ import annotations

import csv
import io
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services import ReportingService, _REPORT_CACHE


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestDailySummaryEndpoint:
    def test_valid_date(self, client: TestClient):
        resp = client.get("/v1/reports/daily-summary", params={"date": "2026-01-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["txn_count"] == 12_840
        assert data["date"] == "2026-01-01"

    def test_invalid_date_returns_fallback(self, client: TestClient):
        resp = client.get("/v1/reports/daily-summary", params={"date": "bad"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["date"] == "bad"
        assert data["items"] == []

    def test_missing_date_param_returns_422(self, client: TestClient):
        resp = client.get("/v1/reports/daily-summary")
        assert resp.status_code == 422


class TestCtrEndpoint:
    def test_valid_date(self, client: TestClient):
        resp = client.get("/v1/reports/ctr", params={"date": "2026-05-20"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["entries"]) == 3

    def test_invalid_date_returns_fallback(self, client: TestClient):
        resp = client.get("/v1/reports/ctr", params={"date": "nope"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries"] == []


class TestSarCandidatesEndpoint:
    def test_valid_date(self, client: TestClient):
        resp = client.get("/v1/reports/sar-candidates", params={"since": "2026-01-10"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["candidates"]) == 2

    def test_invalid_date_returns_fallback(self, client: TestClient):
        resp = client.get("/v1/reports/sar-candidates", params={"since": "invalid"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["candidates"] == []

    def test_missing_since_param_returns_422(self, client: TestClient):
        resp = client.get("/v1/reports/sar-candidates")
        assert resp.status_code == 422


class TestExportEndpoint:
    def test_export_json(self, client: TestClient, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            mock_settings.audit_service_url = "http://localhost:8089"
            mock_settings.service_name = "reporting-service"
            # First generate a report
            client.get("/v1/reports/daily-summary", params={"date": "2026-01-01"})
            resp = client.get(
                "/v1/reports/export",
                params={"reportId": "daily-2026-01-01", "format": "json"},
            )
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "application/json"
            data = json.loads(resp.content)
            assert data["txn_count"] == 12_840

    def test_export_csv(self, client: TestClient, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            mock_settings.audit_service_url = "http://localhost:8089"
            mock_settings.service_name = "reporting-service"
            client.get("/v1/reports/daily-summary", params={"date": "2026-01-01"})
            resp = client.get(
                "/v1/reports/export",
                params={"reportId": "daily-2026-01-01", "format": "csv"},
            )
            assert resp.status_code == 200
            assert "text/csv" in resp.headers["content-type"]

    def test_export_content_disposition_header(self, client: TestClient, tmp_path):
        with patch("app.services.settings") as mock_settings:
            mock_settings.reports_dir = str(tmp_path)
            mock_settings.audit_service_url = "http://localhost:8089"
            mock_settings.service_name = "reporting-service"
            client.get("/v1/reports/daily-summary", params={"date": "2026-01-01"})
            resp = client.get(
                "/v1/reports/export",
                params={"reportId": "daily-2026-01-01", "format": "json"},
            )
            assert "content-disposition" in resp.headers
            assert "daily-2026-01-01.json" in resp.headers["content-disposition"]


class TestExceptionHandlers:
    def test_not_found_handler(self, client: TestClient):
        from app.main import app as test_app
        from fastapi import APIRouter
        from finspoly_commons import NotFoundError

        temp_router = APIRouter()

        @temp_router.get("/_test_not_found")
        def _raise_not_found():
            raise NotFoundError("test not found")

        test_app.include_router(temp_router)
        resp = client.get("/_test_not_found")
        assert resp.status_code == 404
        assert resp.json()["code"] == "NOT_FOUND"

    def test_validation_handler(self, client: TestClient):
        from app.main import app as test_app
        from fastapi import APIRouter
        from finspoly_commons import ValidationError

        temp_router = APIRouter()

        @temp_router.get("/_test_validation")
        def _raise_validation():
            raise ValidationError("test validation")

        test_app.include_router(temp_router)
        resp = client.get("/_test_validation")
        assert resp.status_code == 400
        assert resp.json()["code"] == "VALIDATION_FAILED"

    def test_unauthorized_handler(self, client: TestClient):
        from app.main import app as test_app
        from fastapi import APIRouter
        from finspoly_commons import UnauthorizedError

        temp_router = APIRouter()

        @temp_router.get("/_test_unauth")
        def _raise_unauth():
            raise UnauthorizedError("test unauth")

        test_app.include_router(temp_router)
        resp = client.get("/_test_unauth")
        assert resp.status_code == 401
        assert resp.json()["code"] == "UNAUTHORIZED"

    def test_domain_error_handler(self, client: TestClient):
        from app.main import app as test_app
        from fastapi import APIRouter
        from finspoly_commons import DomainError

        temp_router = APIRouter()

        @temp_router.get("/_test_domain")
        def _raise_domain():
            raise DomainError("test domain error")

        test_app.include_router(temp_router)
        resp = client.get("/_test_domain")
        assert resp.status_code == 500
        assert resp.json()["code"] == "DOMAIN_ERROR"
