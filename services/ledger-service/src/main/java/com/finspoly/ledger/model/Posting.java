package com.finspoly.ledger.model;

import com.finspoly.commons.money.Money;

import java.time.Instant;

public record Posting(
        String id,
        String debitAccountId,
        String creditAccountId,
        Money amount,
        String narrative,
        Instant ts
) {}
