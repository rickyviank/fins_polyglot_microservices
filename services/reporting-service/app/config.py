from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    audit_service_url: str = os.getenv("AUDIT_SERVICE_URL", "http://localhost:8089")
    txn_service_url: str = os.getenv("TXN_SERVICE_URL", "http://localhost:8081")
    fraud_service_url: str = os.getenv("FRAUD_SERVICE_URL", "http://localhost:8088")
    reports_dir: str = os.getenv("REPORTS_DIR", "/tmp/reports")
    service_name: str = "reporting-service"


settings = Settings()
