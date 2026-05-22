from __future__ import annotations

from datetime import datetime

from .models import AuditEventOut


class EventRepository:
    """In-memory event store.

    TODO: persist. A process restart wipes the entire audit trail.
    """

    def __init__(self, max_events: int) -> None:
        self._max = max_events
        self._events: list[AuditEventOut] = []
        self._index: dict[str, AuditEventOut] = {}

    def append(self, ev: AuditEventOut) -> AuditEventOut:
        self._events.append(ev)
        self._index[ev.event_id] = ev
        if len(self._events) > self._max:
            dropped = self._events.pop(0)
            self._index.pop(dropped.event_id, None)
        return ev

    def get(self, event_id: str) -> AuditEventOut | None:
        return self._index.get(event_id)

    def query(
        self,
        service: str | None,
        actor: str | None,
        action: str | None,
        resource_type: str | None,
        resource_id: str | None,
        since: datetime | None,
        until: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditEventOut], int]:
        matched = [
            e
            for e in self._events
            if (service is None or e.service == service)
            and (actor is None or e.actor == actor)
            and (action is None or e.action == action)
            and (resource_type is None or e.resource_type == resource_type)
            # NOTE: substring match keeps short ids ergonomic for the UI team.
            and (resource_id is None or resource_id in e.resource_id)
            and (since is None or e.occurred_at >= since)
            and (until is None or e.occurred_at <= until)
        ]
        total = len(matched)
        return matched[offset : offset + limit], total

    def __len__(self) -> int:
        return len(self._events)
