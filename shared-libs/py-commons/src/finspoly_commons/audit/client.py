from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

Outcome = Literal["success", "failure", "denied"]


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service: str
    actor: str
    action: str
    resource_type: str
    resource_id: str
    outcome: Outcome
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditClient:
    """Best-effort HTTP audit emitter. Never raises out."""

    def __init__(self, audit_service_url: str, service: str, timeout_s: float = 0.5):
        self._url = audit_service_url.rstrip("/")
        self._service = service
        self._timeout = timeout_s

    def emit(
        self,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: Outcome,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = AuditEvent(
            service=self._service,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            metadata=metadata or {},
        )
        try:
            with httpx.Client(timeout=self._timeout) as c:
                c.post(f"{self._url}/v1/events", json=event.model_dump(mode="json"))
        except Exception as ex:  # noqa: BLE001
            log.warning(
                "audit emit failed action=%s resource=%s/%s err=%s",
                action, resource_type, resource_id, ex,
            )
