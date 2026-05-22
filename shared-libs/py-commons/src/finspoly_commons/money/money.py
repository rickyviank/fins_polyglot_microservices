from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable monetary amount, stored as minor units (e.g. cents)."""

    minor_units: int
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.minor_units, int) or isinstance(self.minor_units, bool):
            raise TypeError("minor_units must be int")
        if not (isinstance(self.currency, str) and len(self.currency) == 3 and self.currency.isalpha()):
            raise ValueError("currency must be ISO-4217 3-letter code")
        object.__setattr__(self, "currency", self.currency.upper())

    def __add__(self, other: "Money") -> "Money":
        self._require_same(other)
        return Money(self.minor_units + other.minor_units, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._require_same(other)
        return Money(self.minor_units - other.minor_units, self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.minor_units, self.currency)

    @property
    def is_negative(self) -> bool:
        return self.minor_units < 0

    @property
    def is_positive(self) -> bool:
        return self.minor_units > 0

    @property
    def is_zero(self) -> bool:
        return self.minor_units == 0

    def _require_same(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")

    def __str__(self) -> str:
        sign = "-" if self.minor_units < 0 else ""
        abs_units = abs(self.minor_units)
        return f"{self.currency} {sign}{abs_units // 100}.{abs_units % 100:02d}"


def usd(cents: int) -> Money:
    return Money(cents, "USD")
