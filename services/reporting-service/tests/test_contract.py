"""Contract tests using pact-python.

Verifies the contract between reporting-service (consumer) and
audit-log-service (provider) for the POST /v1/events endpoint.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

import pytest
from pact import Consumer, Format, Like, Provider

from finspoly_commons import AuditClient


PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")


@pytest.fixture(scope="module")
def pact():
    consumer = Consumer("reporting-service")
    provider = Provider("audit-log-service")
    pact = consumer.has_pact_with(
        provider,
        pact_dir=PACT_DIR,
        log_dir=os.path.join(os.path.dirname(__file__), "pact_logs"),
    )
    pact.start_service()
    yield pact
    pact.stop_service()


class TestAuditServiceContract:
    """Consumer-side contract: reporting-service → audit-log-service POST /v1/events."""

    def test_emit_report_export_event(self, pact):
        expected_body = {
            "event_id": Like("some-uuid"),
            "occurred_at": Like("2024-06-15T12:00:00+00:00"),
            "service": "reporting-service",
            "actor": "ops",
            "action": "report.export",
            "resource_type": "report",
            "resource_id": Like("daily-2024-06-15"),
            "outcome": "success",
            "metadata": Like({"format": "json"}),
        }

        (
            pact.given("audit-log-service is running")
            .upon_receiving("a report export audit event")
            .with_request("post", "/v1/events", body=expected_body)
            .will_respond_with(201, body=Like({"event_id": "some-uuid"}))
        )

        with pact:
            client = AuditClient(
                audit_service_url=pact.uri,
                service="reporting-service",
                timeout_s=5.0,
            )
            client.emit(
                actor="ops",
                action="report.export",
                resource_type="report",
                resource_id="daily-2024-06-15",
                outcome="success",
                metadata={"format": "json"},
            )

    def test_emit_sar_export_event(self, pact):
        expected_body = {
            "event_id": Like("uuid-val"),
            "occurred_at": Like("2024-06-15T12:00:00+00:00"),
            "service": "reporting-service",
            "actor": "ops",
            "action": "report.export",
            "resource_type": "report",
            "resource_id": Like("sar-2024-06-01"),
            "outcome": "success",
            "metadata": Like({"format": "csv"}),
        }

        (
            pact.given("audit-log-service is running")
            .upon_receiving("a SAR report export audit event")
            .with_request("post", "/v1/events", body=expected_body)
            .will_respond_with(201, body=Like({"event_id": "uuid-val"}))
        )

        with pact:
            client = AuditClient(
                audit_service_url=pact.uri,
                service="reporting-service",
                timeout_s=5.0,
            )
            client.emit(
                actor="ops",
                action="report.export",
                resource_type="report",
                resource_id="sar-2024-06-01",
                outcome="success",
                metadata={"format": "csv"},
            )

    def test_emit_ctr_export_event(self, pact):
        expected_body = {
            "event_id": Like("uuid-val"),
            "occurred_at": Like("2024-06-15T12:00:00+00:00"),
            "service": "reporting-service",
            "actor": "ops",
            "action": "report.export",
            "resource_type": "report",
            "resource_id": Like("ctr-2024-07-04"),
            "outcome": "success",
            "metadata": Like({"format": "json"}),
        }

        (
            pact.given("audit-log-service is running")
            .upon_receiving("a CTR report export audit event")
            .with_request("post", "/v1/events", body=expected_body)
            .will_respond_with(201, body=Like({"event_id": "uuid-val"}))
        )

        with pact:
            client = AuditClient(
                audit_service_url=pact.uri,
                service="reporting-service",
                timeout_s=5.0,
            )
            client.emit(
                actor="ops",
                action="report.export",
                resource_type="report",
                resource_id="ctr-2024-07-04",
                outcome="success",
                metadata={"format": "json"},
            )

    def test_emit_failure_outcome_event(self, pact):
        expected_body = {
            "event_id": Like("uuid-val"),
            "occurred_at": Like("2024-06-15T12:00:00+00:00"),
            "service": "reporting-service",
            "actor": "ops",
            "action": "report.export",
            "resource_type": "report",
            "resource_id": Like("daily-2024-01-01"),
            "outcome": "failure",
            "metadata": Like({}),
        }

        (
            pact.given("audit-log-service is running")
            .upon_receiving("a failed report export audit event")
            .with_request("post", "/v1/events", body=expected_body)
            .will_respond_with(201, body=Like({"event_id": "uuid-val"}))
        )

        with pact:
            client = AuditClient(
                audit_service_url=pact.uri,
                service="reporting-service",
                timeout_s=5.0,
            )
            client.emit(
                actor="ops",
                action="report.export",
                resource_type="report",
                resource_id="daily-2024-01-01",
                outcome="failure",
                metadata={},
            )
