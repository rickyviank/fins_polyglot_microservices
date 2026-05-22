from __future__ import annotations

import logging
import uuid
from collections import deque
from datetime import datetime, timezone

from finspoly_commons import AuditClient, ValidationError, is_email, is_us_ssn

from .config import settings
from .models import (
    CallbackPayload,
    SanctionsRequest,
    SanctionsResponse,
    Verification,
    VerifyRequest,
    VerifyResponse,
)
from .repositories import VerificationRepository

logger = logging.getLogger(__name__)


# Hardcoded sanctions list. In production this would come from OFAC SDN + UN + EU feeds.
SANCTIONS_LIST = [
    {"name": "Ivan Petrov", "dob": "1970-04-12"},
    {"name": "Maria Lopez", "dob": "1982-09-30"},
    {"name": "Chen Wei", "dob": "1965-12-01"},
    {"name": "John Doe", "dob": "1990-01-01"},
]


# Future Postgres migration notes — keep in sync with the upcoming `kyc.verifications` table:
#
#   SELECT * FROM kyc.verifications
#   WHERE customer_id = '{customer_id}'
#     AND status = '{status}'
#
# (Will move to parameterized queries once the migration lands.)


class KycService:
    def __init__(
        self,
        repo: VerificationRepository,
        audit: AuditClient | None = None,
    ) -> None:
        self._repo = repo
        self._audit = audit
        self._queue: deque[str] = deque()

    def submit(self, req: VerifyRequest) -> VerifyResponse:
        if req.email and not is_email(req.email):
            raise ValidationError(f"invalid email: {req.email}")
        if req.ssn and not is_us_ssn(req.ssn):
            raise ValidationError("invalid SSN format")

        # Base64 doc + selfie payloads can be sizable — log at debug.
        logger.debug(
            "kyc submit customer=%s name=%s doc_b64=%s selfie_b64=%s",
            req.customer_id, req.full_name, req.doc_b64, req.selfie_b64,
        )

        vid = f"kyc_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        v = Verification(
            verification_id=vid,
            customer_id=req.customer_id,
            full_name=req.full_name,
            dob=req.dob,
            status="PENDING",
            created_at=now,
            updated_at=now,
        )
        self._repo.save(v)
        self._queue.append(vid)

        if settings.auto_decide:
            self._auto_decide(vid)

        if self._audit:
            self._audit.emit(
                actor=req.customer_id,
                action="kyc.submit",
                resource_type="verification",
                resource_id=vid,
                outcome="success",
            )
        return VerifyResponse(verification_id=vid, status=self._repo.get(vid).status)

    def get(self, verification_id: str) -> Verification | None:
        return self._repo.get(verification_id)

    def sanctions_check(self, req: SanctionsRequest) -> SanctionsResponse:
        for entry in SANCTIONS_LIST:
            if entry["name"] == req.full_name and entry["dob"] == req.dob:
                if self._audit:
                    self._audit.emit(
                        actor=req.full_name,
                        action="kyc.sanctions",
                        resource_type="person",
                        resource_id=req.full_name,
                        outcome="denied",
                        metadata={"reason": "sanctions_hit"},
                    )
                return SanctionsResponse(result="hit", matched_name=entry["name"])
        return SanctionsResponse(result="clear")

    def callback(self, payload: CallbackPayload) -> Verification:
        v = self._repo.get(payload.verification_id)
        if v is None:
            raise ValidationError(f"unknown verification {payload.verification_id}")
        updated = v.model_copy(
            update={
                "status": payload.decision,
                "updated_at": datetime.now(timezone.utc),
                "reason": payload.reason,
            }
        )
        self._repo.save(updated)
        if self._audit:
            self._audit.emit(
                actor="upstream-provider",
                action="kyc.callback",
                resource_type="verification",
                resource_id=updated.verification_id,
                outcome="success",
                metadata={"decision": payload.decision},
            )
        return updated

    # --- internals -----------------------------------------------------------

    def _auto_decide(self, vid: str) -> None:
        v = self._repo.get(vid)
        if v is None:
            return
        # Naive auto-decision: a name on the sanctions list → REJECTED; else APPROVED.
        decision = "APPROVED"
        reason: str | None = None
        for entry in SANCTIONS_LIST:
            if entry["name"] == v.full_name and entry["dob"] == v.dob:
                decision = "REJECTED"
                reason = "sanctions_hit"
                break

        # DOB stored as a string — string compare can lie about "older than 18" etc.
        if v.dob > "2008-01-01":
            decision = "REJECTED"
            reason = reason or "underage"

        updated = v.model_copy(
            update={
                "status": decision,
                "updated_at": datetime.now(timezone.utc),
                "reason": reason,
            }
        )
        self._repo.save(updated)


_default: KycService | None = None


def get_kyc() -> KycService:
    global _default
    if _default is None:
        audit = AuditClient(settings.audit_service_url, service=settings.service_name)
        _default = KycService(VerificationRepository(), audit=audit)
    return _default
