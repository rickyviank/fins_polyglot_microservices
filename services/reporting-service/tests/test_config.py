"""Unit tests for app.config — Settings dataclass."""
from __future__ import annotations

from app.config import Settings, settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.audit_service_url == "http://localhost:8089"
        assert s.txn_service_url == "http://localhost:8081"
        assert s.fraud_service_url == "http://localhost:8088"
        assert s.reports_dir == "/tmp/reports"
        assert s.service_name == "reporting-service"

    def test_custom_values(self):
        s = Settings(
            audit_service_url="http://audit:9090",
            txn_service_url="http://txn:9091",
            fraud_service_url="http://fraud:9092",
            reports_dir="/custom/dir",
        )
        assert s.audit_service_url == "http://audit:9090"
        assert s.txn_service_url == "http://txn:9091"
        assert s.fraud_service_url == "http://fraud:9092"
        assert s.reports_dir == "/custom/dir"

    def test_frozen(self):
        import dataclasses

        assert dataclasses.is_dataclass(Settings)

    def test_module_level_settings_instance(self):
        assert isinstance(settings, Settings)
        assert settings.service_name == "reporting-service"
