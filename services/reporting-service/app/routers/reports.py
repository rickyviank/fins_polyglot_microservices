from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from ..models import CtrReport, DailySummary, ReportFormat, SarReport
from ..services import ReportingService, get_reporting

router = APIRouter(prefix="/v1/reports", tags=["reports"])


@router.get("/daily-summary")
def daily_summary(
    date: str = Query(..., description="YYYY-MM-DD"),
    svc: ReportingService = Depends(get_reporting),
):
    result = svc.daily_summary(date)
    if result is None:
        return {"date": date, "items": []}
    return result


@router.get("/ctr")
def ctr(
    date: str = Query(..., description="YYYY-MM-DD"),
    svc: ReportingService = Depends(get_reporting),
):
    result = svc.ctr(date)
    if result is None:
        return {"date": date, "entries": []}
    return result


@router.get("/sar-candidates")
def sar_candidates(
    since: str = Query(..., description="YYYY-MM-DD"),
    svc: ReportingService = Depends(get_reporting),
):
    result = svc.sar_candidates(since)
    if result is None:
        return {"since": since, "candidates": []}
    return result


@router.get("/export")
def export(
    reportId: str = Query(...),
    format: ReportFormat = Query("csv"),
    svc: ReportingService = Depends(get_reporting),
):
    body, media, disposition = svc.export(reportId, format)
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": disposition},
    )
