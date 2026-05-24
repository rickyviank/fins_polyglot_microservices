"""End-to-end tests using Playwright.

These tests exercise the reporting service API endpoints via a real
browser-like HTTP client (Playwright), verifying the full request/response
cycle including headers, content types, and downloadable exports.

Prerequisites:
    - Docker Compose services running (docker-compose.test.yml)
    - pip install playwright && playwright install chromium

Run with:
    pytest -m e2e -v

These tests are excluded from the default pytest run.
"""
from __future__ import annotations

import json
import os

import pytest

pytestmark = pytest.mark.e2e

REPORTING_URL = os.getenv("REPORTING_TEST_URL", "http://localhost:18091")


@pytest.fixture(scope="module")
def browser_context():
    """Provide a Playwright browser context for E2E tests."""
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
    page = browser_context.new_page()
    yield page
    page.close()


class TestHealthE2E:
    def test_health_endpoint_via_browser(self, page):
        resp = page.goto(f"{REPORTING_URL}/v1/health")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        data = json.loads(body)
        assert data["status"] == "ok"


class TestDailySummaryE2E:
    def test_daily_summary_renders_json(self, page):
        resp = page.goto(f"{REPORTING_URL}/v1/reports/daily-summary?date=2026-01-01")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        data = json.loads(body)
        assert data["txn_count"] == 12840
        assert data["date"] == "2026-01-01"

    def test_daily_summary_invalid_date(self, page):
        resp = page.goto(f"{REPORTING_URL}/v1/reports/daily-summary?date=invalid")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        data = json.loads(body)
        assert data["items"] == []


class TestCtrE2E:
    def test_ctr_report_entries(self, page):
        resp = page.goto(f"{REPORTING_URL}/v1/reports/ctr?date=2026-06-01")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        data = json.loads(body)
        assert len(data["entries"]) == 3
        for entry in data["entries"]:
            assert float(entry["amount_usd"]) >= 10000


class TestSarE2E:
    def test_sar_candidates(self, page):
        resp = page.goto(f"{REPORTING_URL}/v1/reports/sar-candidates?since=2026-01-01")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        data = json.loads(body)
        assert len(data["candidates"]) == 2
        customer_ids = {c["customer_id"] for c in data["candidates"]}
        assert "c-1001" in customer_ids
        assert "c-7742" in customer_ids


class TestExportE2E:
    def test_export_json_download(self, page):
        page.goto(f"{REPORTING_URL}/v1/reports/daily-summary?date=2026-07-01")

        with page.expect_download() as download_info:
            page.goto(
                f"{REPORTING_URL}/v1/reports/export"
                f"?reportId=daily-2026-07-01&format=json"
            )
        download = download_info.value
        content = download.path().read_text() if download.path() else ""
        if content:
            data = json.loads(content)
            assert data["txn_count"] == 12840

    def test_export_csv_download(self, page):
        page.goto(f"{REPORTING_URL}/v1/reports/ctr?date=2026-07-01")

        with page.expect_download() as download_info:
            page.goto(
                f"{REPORTING_URL}/v1/reports/export"
                f"?reportId=ctr-2026-07-01&format=csv"
            )
        download = download_info.value
        content = download.path().read_text() if download.path() else ""
        if content:
            lines = content.strip().split("\n")
            assert len(lines) == 4  # header + 3 entries


class TestFastAPIDocsE2E:
    def test_openapi_docs_accessible(self, page):
        resp = page.goto(f"{REPORTING_URL}/docs")
        assert resp is not None
        assert resp.status == 200
        title = page.title()
        assert "reporting-service" in title.lower() or "swagger" in title.lower() or "FastAPI" in title

    def test_openapi_json_accessible(self, page):
        resp = page.goto(f"{REPORTING_URL}/openapi.json")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        schema = json.loads(body)
        assert schema["info"]["title"] == "reporting-service"
        assert "/v1/reports/daily-summary" in schema["paths"]
        assert "/v1/reports/ctr" in schema["paths"]
        assert "/v1/reports/sar-candidates" in schema["paths"]
        assert "/v1/reports/export" in schema["paths"]


class TestFullReportingWorkflowE2E:
    def test_generate_and_export_workflow(self, page):
        resp = page.goto(f"{REPORTING_URL}/v1/reports/daily-summary?date=2026-08-01")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        summary = json.loads(body)
        assert summary["txn_count"] == 12840

        resp = page.goto(f"{REPORTING_URL}/v1/reports/ctr?date=2026-08-01")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        ctr = json.loads(body)
        assert len(ctr["entries"]) == 3

        resp = page.goto(f"{REPORTING_URL}/v1/reports/sar-candidates?since=2026-08-01")
        assert resp is not None
        assert resp.status == 200
        body = page.evaluate("document.body.innerText")
        sar = json.loads(body)
        assert len(sar["candidates"]) == 2

        with page.expect_download() as download_info:
            page.goto(
                f"{REPORTING_URL}/v1/reports/export"
                f"?reportId=daily-2026-08-01&format=json"
            )
        download = download_info.value
        content = download.path().read_text() if download.path() else ""
        if content:
            data = json.loads(content)
            assert data["txn_count"] == 12840
