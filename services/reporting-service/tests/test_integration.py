"""Integration tests — require Docker Compose services to be running.

Run with:
    cd services/reporting-service
    docker compose -f docker-compose.test.yml up -d --build --wait
    pytest -m integration -v
    docker compose -f docker-compose.test.yml down

These tests are excluded from the default pytest run (no -m flag)
by the pytest marker configuration in pyproject.toml.
"""
from __future__ import annotations

import os
import time

import httpx
import pytest

pytestmark = pytest.mark.integration

REPORTING_URL = os.getenv("REPORTING_TEST_URL", "http://localhost:18091")
AUDIT_URL = os.getenv("AUDIT_TEST_URL", "http://localhost:18089")
FRAUD_URL = os.getenv("FRAUD_TEST_URL", "http://localhost:18088")


@pytest.fixture(scope="module")
def wait_for_services():
    """Block until all services respond to health checks."""
    endpoints = [
        (REPORTING_URL, "/v1/health"),
        (AUDIT_URL, "/v1/events/_health"),
        (FRAUD_URL, "/v1/health"),
    ]
    deadline = time.time() + 60
    for base, path in endpoints:
        while time.time() < deadline:
            try:
                r = httpx.get(f"{base}{path}", timeout=2.0)
                if r.status_code == 200:
                    break
            except httpx.ConnectError:
                pass
            time.sleep(1)
        else:
            pytest.fail(f"Service {base}{path} did not become healthy within 60s")


class TestReportingServiceHealth:
    def test_health(self, wait_for_services):
        resp = httpx.get(f"{REPORTING_URL}/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestDailySummaryIntegration:
    def test_returns_summary(self, wait_for_services):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2026-01-15"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "txn_count" in data
        assert data["date"] == "2026-01-15"

    def test_invalid_date(self, wait_for_services):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "invalid"},
        )
        assert resp.status_code == 200
        assert resp.json()["items"] == []


class TestCtrIntegration:
    def test_returns_entries(self, wait_for_services):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/ctr",
            params={"date": "2026-03-01"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["entries"]) == 3
        for entry in data["entries"]:
            assert "txn_id" in entry
            assert "amount_usd" in entry

    def test_entry_amounts_above_10k(self, wait_for_services):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/ctr",
            params={"date": "2026-03-01"},
        )
        data = resp.json()
        for entry in data["entries"]:
            assert float(entry["amount_usd"]) >= 10000.00


class TestSarIntegration:
    def test_returns_candidates(self, wait_for_services):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/sar-candidates",
            params={"since": "2026-01-01"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["candidates"]) == 2

    def test_candidate_scores_above_threshold(self, wait_for_services):
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/sar-candidates",
            params={"since": "2026-01-01"},
        )
        data = resp.json()
        for candidate in data["candidates"]:
            assert candidate["score"] >= 80


class TestExportIntegration:
    def test_export_json(self, wait_for_services):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2026-02-01"},
        )
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2026-02-01", "format": "json"},
        )
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = resp.json()
        assert data["txn_count"] == 12840

    def test_export_csv(self, wait_for_services):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/ctr",
            params={"date": "2026-02-01"},
        )
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "ctr-2026-02-01", "format": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        lines = resp.text.strip().split("\n")
        assert len(lines) == 4  # header + 3 CTR entries

    def test_export_content_disposition(self, wait_for_services):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2026-02-01"},
        )
        resp = httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2026-02-01", "format": "json"},
        )
        assert "content-disposition" in resp.headers
        assert "daily-2026-02-01.json" in resp.headers["content-disposition"]

    def test_export_triggers_audit(self, wait_for_services):
        httpx.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2026-04-01"},
        )
        httpx.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2026-04-01", "format": "json"},
        )
        time.sleep(1)
        resp = httpx.get(
            f"{AUDIT_URL}/v1/events",
            params={"action": "report.export", "resource_id": "daily-2026-04-01"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(
            e["action"] == "report.export" and e["resource_id"] == "daily-2026-04-01"
            for e in data["items"]
        )


class TestCrossServiceAuditTrail:
    def test_multiple_reports_create_audit_trail(self, wait_for_services):
        for d in ["2026-05-01", "2026-05-02", "2026-05-03"]:
            httpx.get(
                f"{REPORTING_URL}/v1/reports/daily-summary",
                params={"date": d},
            )
            httpx.get(
                f"{REPORTING_URL}/v1/reports/export",
                params={"reportId": f"daily-{d}", "format": "json"},
            )

        time.sleep(2)
        resp = httpx.get(
            f"{AUDIT_URL}/v1/events",
            params={"action": "report.export", "service": "reporting-service"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3


class TestDownstreamFraudServiceHealth:
    def test_fraud_service_accessible(self, wait_for_services):
        resp = httpx.get(f"{FRAUD_URL}/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
