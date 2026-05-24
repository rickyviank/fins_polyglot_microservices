from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ReportingService, _REPORT_CACHE


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def svc() -> ReportingService:
    return ReportingService(audit=None)


@pytest.fixture(autouse=True)
def _clear_cache():
    _REPORT_CACHE.clear()
    yield
    _REPORT_CACHE.clear()
