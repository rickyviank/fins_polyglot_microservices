"""Contract tests using pact-python v3.

The reporting service is a consumer of:
  1. audit-log-service  (POST /v1/events)
  2. fraud-detection-service (POST /v1/score, GET /v1/health)
  3. transaction-service (conceptual — currently stubbed)

These tests verify that the requests the reporting service (consumer)
sends match the contract expected by each provider.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from pact import Pact
from pact import match


PACT_DIR = Path(__file__).parent / "pacts"


# ---------------------------------------------------------------------------
# Contract: reporting-service → audit-log-service
# ---------------------------------------------------------------------------
class TestAuditServiceContract:
    """Verify the AuditClient.emit() call from reporting-service matches
    the audit-log-service POST /v1/events contract."""

    def test_emit_audit_event(self):
        pact = Pact("reporting-service", "audit-log-service")
        (
            pact.upon_receiving("a request to append an audit event")
            .with_request("POST", "/v1/events")
            .with_header("Content-Type", "application/json", part="Request")
            .with_body(
                {
                    "event_id": match.uuid(),
                    "occurred_at": match.like("2026-01-01T00:00:00+00:00"),
                    "service": match.string("reporting-service"),
                    "actor": match.string("ops"),
                    "action": match.string("report.export"),
                    "resource_type": match.string("report"),
                    "resource_id": match.string("daily-2026-01-01"),
                    "outcome": match.regex("success", regex=r"^(success|failure|denied)$"),
                    "metadata": match.like({}),
                },
                part="Request",
            )
            .will_respond_with(201)
            .with_body(
                {
                    "event_id": match.uuid(),
                    "occurred_at": match.like("2026-01-01T00:00:00+00:00"),
                    "received_at": match.like("2026-01-01T00:00:00+00:00"),
                    "service": match.string("reporting-service"),
                    "actor": match.string("ops"),
                    "action": match.string("report.export"),
                    "resource_type": match.string("report"),
                    "resource_id": match.string("daily-2026-01-01"),
                    "outcome": match.regex("success", regex=r"^(success|failure|denied)$"),
                    "metadata": match.like({}),
                },
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.post(
                f"{url}/v1/events",
                json={
                    "event_id": "a7e7c5c1-9b1a-4d3e-8f5a-1234567890ab",
                    "occurred_at": "2026-01-01T00:00:00+00:00",
                    "service": "reporting-service",
                    "actor": "ops",
                    "action": "report.export",
                    "resource_type": "report",
                    "resource_id": "daily-2026-01-01",
                    "outcome": "success",
                    "metadata": {},
                },
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code == 201

        pact.write_file(PACT_DIR, overwrite=True)

    def test_emit_failure_outcome(self):
        pact = Pact("reporting-service", "audit-log-service")
        (
            pact.upon_receiving("a request to log a failure audit event")
            .with_request("POST", "/v1/events")
            .with_header("Content-Type", "application/json", part="Request")
            .with_body(
                {
                    "event_id": match.uuid(),
                    "occurred_at": match.like("2026-01-01T00:00:00+00:00"),
                    "service": match.string("reporting-service"),
                    "actor": match.string("ops"),
                    "action": match.string("report.export"),
                    "resource_type": match.string("report"),
                    "resource_id": match.string("unknown-report"),
                    "outcome": match.regex("failure", regex=r"^(success|failure|denied)$"),
                    "metadata": match.like({}),
                },
                part="Request",
            )
            .will_respond_with(201)
            .with_body(
                {
                    "event_id": match.uuid(),
                    "occurred_at": match.like("2026-01-01T00:00:00+00:00"),
                    "received_at": match.like("2026-01-01T00:00:00+00:00"),
                    "service": match.string("reporting-service"),
                    "actor": match.string("ops"),
                    "action": match.string("report.export"),
                    "resource_type": match.string("report"),
                    "resource_id": match.string("unknown-report"),
                    "outcome": match.regex("failure", regex=r"^(success|failure|denied)$"),
                    "metadata": match.like({}),
                },
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.post(
                f"{url}/v1/events",
                json={
                    "event_id": "b8e8d6d2-0c2b-5e4f-9060-2345678901bc",
                    "occurred_at": "2026-01-01T00:00:00+00:00",
                    "service": "reporting-service",
                    "actor": "ops",
                    "action": "report.export",
                    "resource_type": "report",
                    "resource_id": "unknown-report",
                    "outcome": "failure",
                    "metadata": {},
                },
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code == 201

        pact.write_file(PACT_DIR, overwrite=True)


# ---------------------------------------------------------------------------
# Contract: reporting-service → fraud-detection-service
# ---------------------------------------------------------------------------
class TestFraudServiceContract:
    """Verify that when reporting-service calls fraud-detection-service
    (e.g. to fetch scores for SAR generation), the contract is honoured."""

    def test_health_check(self):
        pact = Pact("reporting-service", "fraud-detection-service")
        (
            pact.upon_receiving("a health check request")
            .with_request("GET", "/v1/health")
            .will_respond_with(200)
            .with_body(
                {"status": match.string("ok")},
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.get(f"{url}/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

        pact.write_file(PACT_DIR, overwrite=True)

    def test_score_request(self):
        pact = Pact("reporting-service", "fraud-detection-service")
        (
            pact.upon_receiving("a fraud score request")
            .with_request("POST", "/v1/score")
            .with_header("Content-Type", "application/json", part="Request")
            .with_body(
                {
                    "txnId": match.string("txn-001"),
                    "customerId": match.string("c-1001"),
                    "amount": match.like(12500.00),
                    "merchant": match.string("WIRE_OUT_INTL"),
                    "country": match.regex("US", regex=r"^[A-Z]{2}$"),
                    "timestamp": match.like("2026-01-01T09:12:00+00:00"),
                },
                part="Request",
            )
            .will_respond_with(200)
            .with_body(
                {
                    "txn_id": match.string("txn-001"),
                    "customer_id": match.string("c-1001"),
                    "score": match.integer(88),
                    "decision": match.regex("review", regex=r"^(approve|review|decline)$"),
                    "reasons": match.each_like(
                        {
                            "code": match.string("HIGH_AMOUNT"),
                            "description": match.string("Transaction exceeds threshold"),
                            "weight": match.like(0.75),
                        },
                        min=1,
                    ),
                },
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.post(
                f"{url}/v1/score",
                json={
                    "txnId": "txn-001",
                    "customerId": "c-1001",
                    "amount": 12500.00,
                    "merchant": "WIRE_OUT_INTL",
                    "country": "US",
                    "timestamp": "2026-01-01T09:12:00+00:00",
                },
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "score" in data
            assert data["decision"] in ("approve", "review", "decline")

        pact.write_file(PACT_DIR, overwrite=True)

    def test_get_score_not_found(self):
        pact = Pact("reporting-service", "fraud-detection-service")
        (
            pact.upon_receiving("a request for a non-existent score")
            .with_request("GET", "/v1/scores/txn-nonexistent")
            .will_respond_with(404)
            .with_body(
                {
                    "code": match.string("NOT_FOUND"),
                    "message": match.like("score for txn txn-nonexistent not found"),
                },
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.get(f"{url}/v1/scores/txn-nonexistent")
            assert resp.status_code == 404

        pact.write_file(PACT_DIR, overwrite=True)


# ---------------------------------------------------------------------------
# Contract: reporting-service → transaction-service
# ---------------------------------------------------------------------------
class TestTransactionServiceContract:
    """Verify expected interactions with the transaction-service.
    Currently the reporting-service uses stubbed data, but the contract
    documents the expected shape when real integration is added."""

    def test_health_check(self):
        pact = Pact("reporting-service", "transaction-service")
        (
            pact.upon_receiving("a health check request to transaction service")
            .with_request("GET", "/v1/health")
            .will_respond_with(200)
            .with_body(
                {"status": match.string("ok")},
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.get(f"{url}/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

        pact.write_file(PACT_DIR, overwrite=True)

    def test_list_transactions_for_date(self):
        pact = Pact("reporting-service", "transaction-service")
        (
            pact.upon_receiving("a request to list transactions for a date range")
            .with_request("GET", "/v1/transactions")
            .with_query_parameter("since", match.like("2026-01-01"))
            .with_query_parameter("until", match.like("2026-01-02"))
            .will_respond_with(200)
            .with_body(
                {
                    "items": match.each_like(
                        {
                            "txnId": match.string("txn-001"),
                            "customerId": match.string("c-1001"),
                            "amount": match.integer(1250000),
                            "currency": match.string("USD"),
                            "status": match.regex("SETTLED", regex=r"^(PENDING|SETTLED|DECLINED|REVERSED)$"),
                            "merchant": match.string("WIRE_OUT_INTL"),
                            "createdAt": match.like("2026-01-01T09:12:00Z"),
                        },
                    ),
                    "total": match.integer(1),
                },
                part="Response",
            )
        )

        with pact.serve() as mock_server:
            url = str(mock_server.url)
            resp = httpx.get(
                f"{url}/v1/transactions",
                params={"since": "2026-01-01", "until": "2026-01-02"},
            )
            assert resp.status_code == 200
            assert "items" in resp.json()

        pact.write_file(PACT_DIR, overwrite=True)
