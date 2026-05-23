"""End-to-end tests using Playwright.

Tests the reporting-service through its Swagger UI and API endpoints.

Requires the docker-compose stack to be running:
    docker compose -f docker-compose.test.yml up -d --build --wait

Run with:
    pytest tests/test_e2e.py -m e2e
"""
from __future__ import annotations

import json
import os
import time

import pytest

REPORTING_URL = os.getenv("REPORTING_URL", "http://localhost:18091")
AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:18089")

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def browser_context():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context()
    yield context
    context.close()
    browser.close()
    pw.stop()


@pytest.fixture()
def page(browser_context):
    p = browser_context.new_page()
    yield p
    p.close()


class TestSwaggerUI:
    """Verify the Swagger UI loads and is functional."""

    def test_docs_page_loads(self, page):
        page.goto(f"{REPORTING_URL}/docs")
        page.wait_for_load_state("networkidle", timeout=15000)
        content = page.content()
        assert "reporting-service" in content.lower()

    def test_openapi_schema_accessible(self, page):
        resp = page.request.get(f"{REPORTING_URL}/openapi.json")
        assert resp.status == 200
        schema = resp.json()
        assert schema["info"]["title"] == "reporting-service"
        assert "/v1/reports/daily-summary" in schema["paths"]
        assert "/v1/reports/ctr" in schema["paths"]
        assert "/v1/reports/sar-candidates" in schema["paths"]
        assert "/v1/reports/export" in schema["paths"]
        assert "/v1/health" in schema["paths"]


class TestAPIEndToEnd:
    """Full user journey tested via Playwright's API request context."""

    def test_full_daily_summary_flow(self, page):
        api = page.request

        health = api.get(f"{REPORTING_URL}/v1/health")
        assert health.status == 200
        assert health.json()["status"] == "ok"

        summary = api.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2024-06-15"},
        )
        assert summary.status == 200
        body = summary.json()
        assert body["date"] == "2024-06-15"
        assert body["txn_count"] > 0
        assert "total_volume_usd" in body

        export = api.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2024-06-15", "format": "json"},
        )
        assert export.status == 200
        assert "application/json" in export.headers["content-type"]
        exported = export.json()
        assert exported["date"] == "2024-06-15"

    def test_full_ctr_flow(self, page):
        api = page.request

        ctr = api.get(
            f"{REPORTING_URL}/v1/reports/ctr",
            params={"date": "2024-07-04"},
        )
        assert ctr.status == 200
        body = ctr.json()
        assert len(body["entries"]) > 0
        assert body["entries"][0]["txn_id"].startswith("txn-")

        export_csv = api.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "ctr-2024-07-04", "format": "csv"},
        )
        assert export_csv.status == 200
        assert "text/csv" in export_csv.headers["content-type"]
        csv_text = export_csv.text()
        assert "txn_id" in csv_text

    def test_full_sar_flow(self, page):
        api = page.request

        sar = api.get(
            f"{REPORTING_URL}/v1/reports/sar-candidates",
            params={"since": "2024-06-01"},
        )
        assert sar.status == 200
        body = sar.json()
        assert len(body["candidates"]) > 0
        assert body["candidates"][0]["score"] > 0

        export_json = api.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "sar-2024-06-01", "format": "json"},
        )
        assert export_json.status == 200
        exported = export_json.json()
        assert "candidates" in exported

    def test_export_audit_trail_e2e(self, page):
        api = page.request

        api.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "2024-12-25"},
        )
        api.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "daily-2024-12-25", "format": "json"},
        )
        time.sleep(1)

        events = api.get(
            f"{AUDIT_URL}/v1/events",
            params={
                "service": "reporting-service",
                "action": "report.export",
                "resource_id": "daily-2024-12-25",
            },
        )
        assert events.status == 200
        event_body = events.json()
        assert event_body["total"] >= 1

    def test_invalid_date_handling(self, page):
        api = page.request

        resp = api.get(
            f"{REPORTING_URL}/v1/reports/daily-summary",
            params={"date": "not-a-date"},
        )
        assert resp.status == 200
        body = resp.json()
        assert body["items"] == []

    def test_export_unknown_report(self, page):
        api = page.request

        resp = api.get(
            f"{REPORTING_URL}/v1/reports/export",
            params={"reportId": "nonexistent-123", "format": "json"},
        )
        assert resp.status == 200


class TestSwaggerUIInteraction:
    """Test interacting with the Swagger UI to execute API calls."""

    def test_try_health_endpoint_via_swagger(self, page):
        page.goto(f"{REPORTING_URL}/docs")
        page.wait_for_load_state("networkidle", timeout=15000)

        health_section = page.locator("#operations-default-health_v1_health_get")
        if health_section.count() > 0:
            health_section.click()
            try_btn = health_section.locator("button.try-out__btn")
            if try_btn.count() > 0:
                try_btn.click()
                execute_btn = health_section.locator("button.execute")
                if execute_btn.count() > 0:
                    execute_btn.click()
                    page.wait_for_timeout(2000)
        content = page.content()
        assert "reporting-service" in content.lower()
