package com.finspoly.account.dto;

import com.finspoly.account.model.Account;

import java.time.Instant;

public record AccountResponse(
        String accountNumber,
        String customerId,
        String type,
        long balanceMinorUnits,
        String currency,
        String status,
        Instant openedAt
) {
    public static AccountResponse from(Account a) {
        return new AccountResponse(
                a.accountNumber(),
                a.customerId(),
                a.type().name(),
                a.balance().minorUnits(),
                a.balance().currency(),
                a.status().name(),
                a.openedAt());
    }
}
