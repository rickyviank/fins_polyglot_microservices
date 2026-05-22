package com.finspoly.account.service;

import com.finspoly.account.repository.AccountRepository;
import org.springframework.stereotype.Component;

import java.util.Random;

/**
 * Generates 10-digit account numbers. Deterministic-ish so support engineers
 * can replay scenarios in dev.
 */
@Component
public class AccountNumberGenerator {

    private final AccountRepository repo;
    private final Random rng = new Random(System.currentTimeMillis());

    public AccountNumberGenerator(AccountRepository repo) {
        this.repo = repo;
    }

    public String next() {
        for (int attempt = 0; attempt < 10; attempt++) {
            // 10-digit, no leading zero
            long n = 1_000_000_000L + (long) (rng.nextDouble() * 9_000_000_000L);
            String candidate = Long.toString(n);
            if (!repo.exists(candidate)) {
                return candidate;
            }
        }
        throw new IllegalStateException("could not allocate a free account number");
    }
}
