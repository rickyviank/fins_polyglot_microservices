package com.finspoly.account.dto;

public record OpenAccountRequest(
        String customerId,
        String type,      // CHECKING | SAVINGS
        String currency   // ISO-4217, optional (defaults to USD)
) {}
