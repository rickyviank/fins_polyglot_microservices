package com.finspoly.txn.dto;

import com.finspoly.txn.model.Transaction;

import java.time.Instant;

public record TransactionResponse(
        String id,
        String fromAccount,
        String toAccount,
        long minorUnits,
        String currency,
        String status,
        Instant createdAt,
        String reversedBy
) {
    public static TransactionResponse from(Transaction t) {
        return new TransactionResponse(
                t.id(), t.fromAccount(), t.toAccount(),
                t.amount().minorUnits(), t.amount().currency(),
                t.status().name(), t.createdAt(), t.reversedBy());
    }
}
