from __future__ import annotations

from fastapi.testclient import TestClient

import app.services as services_mod
from app.main import app
from app.repositories import VerificationRepository
from app.services import KycService


def test_sanctions_hit_on_exact_match(monkeypatch):
    monkeypatch.setattr(services_mod, "_default", KycService(VerificationRepository(), audit=None))
    client = TestClient(app)
    r = client.post(
        "/v1/kyc/sanctions-check",
        json={"fullName": "Ivan Petrov", "dob": "1970-04-12"},
    )
    assert r.status_code == 200
    assert r.json()["result"] == "hit"
