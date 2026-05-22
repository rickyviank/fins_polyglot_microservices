from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

Outcome = Literal["success", "failure", "denied"]


class AuditEventIn(BaseModel):
    """Mirror of finspoly_commons.AuditEvent, accepted from any service."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str
    actor: str
    action: str
    resource_type: str
    resource_id: str
    outcome: Outcome
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventOut(AuditEventIn):
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventPage(BaseModel):
    items: list[AuditEventOut]
    total: int
    limit: int
    offset: int
