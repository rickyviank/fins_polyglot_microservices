"""Unit tests for reporting-service Settings configuration."""
from __future__ import annotations

import os
from unittest.mock import patch

from app.config import Settings


class TestSettings:
    def test_default_values(self):
        with patch.dict(os.environ, {}, clear=True):
            s = Settings()
        assert s.audit_service_url == "http://localhost:8089"
        assert s.txn_service_url == "http://localhost:8081"
        assert s.fraud_service_url == "http://localhost:8088"
        assert s.reports_dir == "/tmp/reports"
        assert s.service_name == "reporting-service"

    def test_custom_env_overrides(self):
        env = {
            "AUDIT_SERVICE_URL": "http://audit:9090",
            "TXN_SERVICE_URL": "http://txn:9091",
            "FRAUD_SERVICE_URL": "http://fraud:9092",
            "REPORTS_DIR": "/data/reports",
        }
        with patch.dict(os.environ, env):
            s = Settings(
                audit_service_url=os.getenv("AUDIT_SERVICE_URL", ""),
                txn_service_url=os.getenv("TXN_SERVICE_URL", ""),
                fraud_service_url=os.getenv("FRAUD_SERVICE_URL", ""),
                reports_dir=os.getenv("REPORTS_DIR", ""),
            )
        assert s.audit_service_url == "http://audit:9090"
        assert s.txn_service_url == "http://txn:9091"
        assert s.fraud_service_url == "http://fraud:9092"
        assert s.reports_dir == "/data/reports"

    def test_frozen_settings(self):
        s = Settings()
        import dataclasses
        assert dataclasses.is_dataclass(s)
        assert s.__dataclass_params__.frozen  # type: ignore[attr-defined]
