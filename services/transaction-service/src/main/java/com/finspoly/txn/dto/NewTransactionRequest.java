package com.finspoly.txn.dto;

public record NewTransactionRequest(
        String fromAccount,
        String toAccount,
        long minorUnits,
        String currency,
        String expectedCurrency,
        String idempotencyKey
) {}
