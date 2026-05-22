package com.finspoly.ledger.dto;

public record PostingRequest(
        String debitAccountId,
        String creditAccountId,
        long minorUnits,
        Long debitMinorUnits,    // optional; defaults to minorUnits if absent
        Long creditMinorUnits,   // optional; defaults to minorUnits if absent
        String currency,
        String narrative
) {}
