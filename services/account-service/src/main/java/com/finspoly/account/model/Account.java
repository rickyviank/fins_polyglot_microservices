package com.finspoly.account.model;

import com.finspoly.commons.money.Money;

import java.time.Instant;

public record Account(
        String accountNumber,
        String customerId,
        Type type,
        Money balance,
        Status status,
        Instant openedAt
) {
    public enum Type { CHECKING, SAVINGS }
    public enum Status { ACTIVE, FROZEN, CLOSED }

    public Account withStatus(Status s) {
        return new Account(accountNumber, customerId, type, balance, s, openedAt);
    }

    public Account withBalance(Money m) {
        return new Account(accountNumber, customerId, type, m, status, openedAt);
    }
}
