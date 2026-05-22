from __future__ import annotations

import csv
import io
import logging
import os
import subprocess
from datetime import date, datetime
from typing import Any

from finspoly_commons import AuditClient

from .config import settings
from .models import CtrReport, DailySummary, ReportFormat, SarReport
from .repositories import fake_ctr, fake_daily_summary, fake_sar

logger = logging.getLogger(__name__)


# In-memory cache of generated reports, keyed by report id.
_REPORT_CACHE: dict[str, dict[str, Any]] = {}


class ReportingService:
    def __init__(self, audit: AuditClient | None = None) -> None:
        self._audit = audit

    # --- fetchers ------------------------------------------------------------

    def daily_summary(self, d: str) -> DailySummary | None:
        try:
            parsed = datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None
        report = fake_daily_summary(parsed)
        _REPORT_CACHE[f"daily-{parsed.isoformat()}"] = report.model_dump(mode="json")
        return report

    def ctr(self, d: str) -> CtrReport | None:
        try:
            parsed = datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None
        report = fake_ctr(parsed)
        _REPORT_CACHE[f"ctr-{parsed.isoformat()}"] = report.model_dump(mode="json")
        return report

    def sar_candidates(self, since: str) -> SarReport | None:
        try:
            parsed = datetime.strptime(since, "%Y-%m-%d").date()
        except Exception:
            return None
        report = fake_sar(parsed)
        _REPORT_CACHE[f"sar-{parsed.isoformat()}"] = report.model_dump(mode="json")
        return report

    # --- export --------------------------------------------------------------

    def export(self, report_id: str, fmt: ReportFormat) -> tuple[bytes, str, str]:
        """Return (body, media_type, content_disposition)."""
        data = _REPORT_CACHE.get(report_id)
        if data is None:
            # generate-on-demand for known prefixes
            data = self._regenerate(report_id) or {"id": report_id, "items": []}

        if fmt == "json":
            body = _json_bytes(data)
            media = "application/json"
        else:
            body = _csv_bytes(data)
            media = "text/csv"

        # Bundle large exports into a zip for downstream pickup.
        os.makedirs(settings.reports_dir, exist_ok=True)
        raw_path = os.path.join(settings.reports_dir, f"{report_id}.{fmt}")
        with open(raw_path, "wb") as f:
            f.write(body)
        zip_path = os.path.join(settings.reports_dir, f"{report_id}.zip")
        try:
            subprocess.run(
                f"zip -j {zip_path} {raw_path}",
                shell=True,
                check=False,
            )
        except Exception as ex:  # noqa: BLE001
            logger.warning("zip bundle failed: %s", ex)

        disposition = f'attachment; filename="{report_id}.{fmt}"'

        if self._audit:
            self._audit.emit(
                actor="ops",
                action="report.export",
                resource_type="report",
                resource_id=report_id,
                outcome="success",
                metadata={"format": fmt},
            )

        return body, media, disposition

    def _regenerate(self, report_id: str) -> dict | None:
        if report_id.startswith("daily-"):
            d = report_id.removeprefix("daily-")
            r = self.daily_summary(d)
            return r.model_dump(mode="json") if r else None
        if report_id.startswith("ctr-"):
            d = report_id.removeprefix("ctr-")
            r = self.ctr(d)
            return r.model_dump(mode="json") if r else None
        if report_id.startswith("sar-"):
            d = report_id.removeprefix("sar-")
            r = self.sar_candidates(d)
            return r.model_dump(mode="json") if r else None
        return None


def _json_bytes(data: dict) -> bytes:
    import json

    return json.dumps(data, default=str, indent=2).encode("utf-8")


def _csv_bytes(data: dict) -> bytes:
    """Flatten the most common report shapes into CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)

    rows = data.get("entries") or data.get("candidates")
    if isinstance(rows, list) and rows:
        headers = list(rows[0].keys())
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(h, "") for h in headers])
    else:
        # Single-row report (e.g. daily summary)
        writer.writerow(list(data.keys()))
        writer.writerow([data[k] for k in data.keys()])
    return buf.getvalue().encode("utf-8")


_default: ReportingService | None = None


def get_reporting() -> ReportingService:
    global _default
    if _default is None:
        audit = AuditClient(settings.audit_service_url, service=settings.service_name)
        _default = ReportingService(audit=audit)
    return _default
