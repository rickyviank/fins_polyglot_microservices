from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    audit_service_url: str = os.getenv("AUDIT_SERVICE_URL", "http://localhost:8089")
    velocity_window_min: int = int(os.getenv("VELOCITY_WINDOW_MIN", "5"))
    velocity_threshold: int = int(os.getenv("VELOCITY_THRESHOLD", "5"))
    high_amount_usd: int = int(os.getenv("HIGH_AMOUNT_USD", "10000"))
    service_name: str = "fraud-detection-service"


settings = Settings()
