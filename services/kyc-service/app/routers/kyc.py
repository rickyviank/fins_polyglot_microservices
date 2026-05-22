from __future__ import annotations

from fastapi import APIRouter, Depends

from finspoly_commons import NotFoundError

from ..models import (
    CallbackPayload,
    SanctionsRequest,
    SanctionsResponse,
    Verification,
    VerifyRequest,
    VerifyResponse,
)
from ..services import KycService, get_kyc

router = APIRouter(prefix="/v1/kyc", tags=["kyc"])


@router.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest, svc: KycService = Depends(get_kyc)) -> VerifyResponse:
    return svc.submit(req)


@router.get("/{verification_id}", response_model=Verification)
def get_verification(verification_id: str, svc: KycService = Depends(get_kyc)) -> Verification:
    v = svc.get(verification_id)
    if not v:
        raise NotFoundError(f"verification {verification_id} not found")
    return v


@router.post("/sanctions-check", response_model=SanctionsResponse)
def sanctions_check(req: SanctionsRequest, svc: KycService = Depends(get_kyc)) -> SanctionsResponse:
    return svc.sanctions_check(req)


@router.post("/callback", response_model=Verification)
def callback(payload: CallbackPayload, svc: KycService = Depends(get_kyc)) -> Verification:
    return svc.callback(payload)
