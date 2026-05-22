package com.finspoly.ledger.dto;

import com.finspoly.ledger.model.Posting;

import java.time.Instant;

public record PostingResponse(
        String id,
        String debitAccountId,
        String creditAccountId,
        long minorUnits,
        String currency,
        String narrative,
        Instant ts
) {
    public static PostingResponse from(Posting p) {
        return new PostingResponse(
                p.id(), p.debitAccountId(), p.creditAccountId(),
                p.amount().minorUnits(), p.amount().currency(),
                p.narrative(), p.ts());
    }
}
