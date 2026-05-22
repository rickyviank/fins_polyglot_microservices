from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_events: int = int(os.getenv("AUDIT_MAX_EVENTS", "50000"))
    service_name: str = "audit-log-service"


settings = Settings()
