package com.finspoly.txn.model;

import com.finspoly.commons.money.Money;

import java.time.Instant;

public record Transaction(
        String id,
        String fromAccount,
        String toAccount,
        Money amount,
        Status status,
        String idempotencyKey,
        Instant createdAt,
        String reversedBy
) {
    public enum Status { PENDING, POSTED, REVERSED, FAILED }

    public Transaction withStatus(Status newStatus) {
        return new Transaction(id, fromAccount, toAccount, amount, newStatus, idempotencyKey, createdAt, reversedBy);
    }

    public Transaction withReversedBy(String reversalId) {
        return new Transaction(id, fromAccount, toAccount, amount, Status.REVERSED, idempotencyKey, createdAt, reversalId);
    }
}
