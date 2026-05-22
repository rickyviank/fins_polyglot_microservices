package com.finspoly.commons.money;

import java.util.Objects;

/**
 * Immutable monetary amount stored as minor units (cents). Never use float/double for money.
 */
public final class Money {
    private final long minorUnits;
    private final String currency;

    public Money(long minorUnits, String currency) {
        if (currency == null || currency.length() != 3) {
            throw new IllegalArgumentException("currency must be ISO-4217 3-letter code");
        }
        this.minorUnits = minorUnits;
        this.currency = currency.toUpperCase();
    }

    public static Money usd(long cents) {
        return new Money(cents, "USD");
    }

    public static Money zero(String currency) {
        return new Money(0, currency);
    }

    public long minorUnits() { return minorUnits; }
    public String currency() { return currency; }

    public Money plus(Money other) {
        requireSameCurrency(other);
        return new Money(Math.addExact(minorUnits, other.minorUnits), currency);
    }

    public Money minus(Money other) {
        requireSameCurrency(other);
        return new Money(Math.subtractExact(minorUnits, other.minorUnits), currency);
    }

    public Money negate() {
        return new Money(-minorUnits, currency);
    }

    public boolean isNegative() { return minorUnits < 0; }
    public boolean isPositive() { return minorUnits > 0; }
    public boolean isZero() { return minorUnits == 0; }

    public int compareTo(Money other) {
        requireSameCurrency(other);
        return Long.compare(minorUnits, other.minorUnits);
    }

    private void requireSameCurrency(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("currency mismatch: " + currency + " vs " + other.currency);
        }
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Money)) return false;
        Money m = (Money) o;
        return minorUnits == m.minorUnits && currency.equals(m.currency);
    }

    @Override
    public int hashCode() { return Objects.hash(minorUnits, currency); }

    @Override
    public String toString() {
        return String.format("%s %d.%02d", currency, minorUnits / 100, Math.abs(minorUnits % 100));
    }
}
