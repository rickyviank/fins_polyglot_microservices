from __future__ import annotations

from .models import Verification


class VerificationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Verification] = {}

    def save(self, v: Verification) -> Verification:
        self._items[v.verification_id] = v
        return v

    def get(self, verification_id: str) -> Verification | None:
        return self._items.get(verification_id)
