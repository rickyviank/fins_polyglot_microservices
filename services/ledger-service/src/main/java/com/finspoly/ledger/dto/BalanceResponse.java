package com.finspoly.ledger.dto;

public record BalanceResponse(
        String accountId,
        long minorUnits,
        String currency
) {}
