"""Integration tests for reporting-service with downstream audit-log-service.

These tests require the docker-compose stack to be running:
    docker compose -f docker-compose.test.yml up -d --build --wait

Run with:
    pytest tests/test_integration.py -m integration
"""
from __future__ import annotations

import json
import os
import time

import httpx
import pytest

REPORTING_URL = os.getenv("REPORTING_URL", "http://localhost:18091")
AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:18089")

pytestmark = pytest.mark.integration


def _wait_for_service(url: str, path: str, timeout: int = 30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{url}{path}", timeout=3)
            if resp.status_code == 200:
                return
        except httpx.ConnectError:
            pass
        time.sleep(1)
    pytest.skip(f"Service at {url} not available")


@pytest.fixture(scope="module", autouse=True)
def _services_ready():
    _wait_for_service(REPORTING_URL, "/v1/health")
    _wait_for_service(AUDIT_URL, "/v1/events/_health")


class TestReportingAuditIntegration:
    """Verify that reporting-service sends audit events to audit-log-service."""

    def test_health_check(self):
        resp = httpx.get(f"{REPORTING_URL}/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_daily_summary_returns_data(self):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2024-06-15"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["date"] == "2024-06-15"
        assert body["txn_count"] > 0

    def test_ctr_report_returns_entries(self):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/ctr",
            params={"date": "2024-07-04"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entries"]) > 0

    def test_sar_report_returns_candidates(self):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/sar-candidates",
            params={"since": "2024-06-01"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["candidates"]) > 0

    def test_export_json_creates_file(self):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2024-08-01"},
        )
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2024-08-01", "format": "json"},
        )
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        body = resp.json()
        assert body["date"] == "2024-08-01"

    def test_export_csv_has_content_disposition(self):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/ctr",
            params={"date": "2024-08-01"},
        )
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "ctr-2024-08-01", "format": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "Content-Disposition" in resp.headers

    def test_export_sends_audit_event_to_audit_service(self):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2024-09-15"},
        )
        httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2024-09-15", "format": "json"},
        )
        time.sleep(1)

        resp = httpx.get(
            f"{AUDIT_URL}/v1/events",
            params={
                "service": "reporting-service",
                "action": "report.export",
                "resource_id": "daily-2024-09-15",
            },
        )
        assert resp.status_code == 200
        events = resp.json()
        assert events["total"] >= 1
        event = events["items"][0]
        assert event["service"] == "reporting-service"
        assert event["action"] == "report.export"
        assert event["outcome"] == "success"

    def test_multiple_exports_create_multiple_audit_events(self):
        for fmt in ("json", "csv"):
            httpx.get(
                f"{REPORTING_URL}/v1/reports/export",
                params={"reportId": "ctr-2024-10-01", "format": fmt},
            )
        time.sleep(1)

        resp = httpx.get(
            f"{AUDIT_URL}/v1/events",
            params={
                "service": "reporting-service",
                "resource_id": "ctr-2024-10-01",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

    def test_sar_export_audit_trail(self):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/sar-candidates",
            params={"since": "2024-11-01"},
        )
        httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "sar-2024-11-01", "format": "csv"},
        )
        time.sleep(1)

        resp = httpx.get(
            f"{AUDIT_URL}/v1/events",
            params={
                "service": "reporting-service",
                "resource_id": "sar-2024-11-01",
            },
        )
        assert resp.status_code == 200
        events = resp.json()
        assert events["total"] >= 1
        assert events["items"][0]["metadata"]["format"] == "csv"
