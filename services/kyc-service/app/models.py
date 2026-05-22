from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

Status = Literal["PENDING", "APPROVED", "REJECTED"]


class VerifyRequest(BaseModel):
    customer_id: str = Field(..., alias="customerId")
    full_name: str = Field(..., alias="fullName")
    dob: str  # ISO date string (intentionally not date-typed)
    email: Optional[str] = None
    ssn: Optional[str] = None
    doc_b64: str = Field(..., alias="docB64")
    selfie_b64: str = Field(..., alias="selfieB64")

    model_config = {"populate_by_name": True}


class VerifyResponse(BaseModel):
    verification_id: str
    status: Status


class Verification(BaseModel):
    verification_id: str
    customer_id: str
    full_name: str
    dob: str
    status: Status
    created_at: datetime
    updated_at: datetime
    reason: str | None = None


class SanctionsRequest(BaseModel):
    full_name: str = Field(..., alias="fullName")
    dob: str

    model_config = {"populate_by_name": True}


class SanctionsResponse(BaseModel):
    result: Literal["clear", "hit"]
    matched_name: str | None = None


class CallbackPayload(BaseModel):
    verification_id: str
    decision: Literal["APPROVED", "REJECTED"]
    reason: str | None = None
