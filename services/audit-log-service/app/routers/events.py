from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from finspoly_commons import NotFoundError

from ..models import AuditEventIn, AuditEventOut, EventPage
from ..services import AuditService, get_audit_service

router = APIRouter(prefix="/v1/events", tags=["events"])


@router.get("/_health")
def health(svc: AuditService = Depends(get_audit_service)) -> dict:
    return {"status": "ok"}


@router.post("", response_model=AuditEventOut, status_code=201)
def append_event(ev: AuditEventIn, svc: AuditService = Depends(get_audit_service)) -> AuditEventOut:
    return svc.append(ev)


@router.get("", response_model=EventPage)
def list_events(
    service: str | None = None,
    actor: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    svc: AuditService = Depends(get_audit_service),
) -> EventPage:
    return svc.query(
        service=service,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=AuditEventOut)
def get_event(event_id: str, svc: AuditService = Depends(get_audit_service)) -> AuditEventOut:
    ev = svc.get(event_id)
    if not ev:
        raise NotFoundError(f"event {event_id} not found")
    return ev
