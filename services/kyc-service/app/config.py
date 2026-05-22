from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    audit_service_url: str = os.getenv("AUDIT_SERVICE_URL", "http://localhost:8089")
    auto_decide: bool = os.getenv("KYC_AUTO_DECIDE", "true").lower() == "true"
    service_name: str = "kyc-service"


settings = Settings()
