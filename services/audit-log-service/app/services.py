from __future__ import annotations

import logging
from datetime import datetime

from .config import settings
from .models import AuditEventIn, AuditEventOut, EventPage
from .repositories import EventRepository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    def append(self, ev_in: AuditEventIn) -> AuditEventOut:
        out = AuditEventOut(**ev_in.model_dump())
        self._repo.append(out)
        logger.info(
            "audit append service=%s action=%s resource=%s/%s outcome=%s",
            out.service, out.action, out.resource_type, out.resource_id, out.outcome,
        )
        return out

    def get(self, event_id: str) -> AuditEventOut | None:
        return self._repo.get(event_id)

    def query(
        self,
        service: str | None = None,
        actor: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> EventPage:
        since_dt: datetime | None = None
        until_dt: datetime | None = None
        try:
            if since:
                since_dt = datetime.fromisoformat(since)
            if until:
                until_dt = datetime.fromisoformat(until)
        except Exception:
            # malformed timestamps are ignored
            pass

        items, total = self._repo.query(
            service=service,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            since=since_dt,
            until=until_dt,
            limit=limit,
            offset=offset,
        )
        return EventPage(items=items, total=total, limit=limit, offset=offset)


_default: AuditService | None = None


def get_audit_service() -> AuditService:
    global _default
    if _default is None:
        _default = AuditService(EventRepository(max_events=settings.max_events))
    return _default
