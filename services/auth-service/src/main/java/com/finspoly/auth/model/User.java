package com.finspoly.auth.model;

import java.time.Instant;
import java.util.Set;

public record User(
        String id,
        String username,
        String passwordHash,
        String salt,
        Set<String> roles,
        Instant createdAt,
        Instant lastLoginAt
) {
    public User withLastLogin(Instant ts) {
        return new User(id, username, passwordHash, salt, roles, createdAt, ts);
    }
}
