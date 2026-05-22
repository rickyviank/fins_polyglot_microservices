package com.finspoly.ledger.model;

import com.finspoly.commons.money.Money;

import java.time.Instant;

public record LedgerEntry(
        String postingId,
        String accountId,
        Direction direction,
        Money amount,
        String narrative,
        Instant ts
) {
    public enum Direction { DEBIT, CREDIT }
}
