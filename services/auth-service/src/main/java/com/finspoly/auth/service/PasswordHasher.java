package com.finspoly.auth.service;

import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/**
 * Hashes passwords for storage. Returns a hex-encoded SHA-256 digest.
 */
@Component
public class PasswordHasher {

    public String hash(String plain) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(plain.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            // SHA-256 is mandated by the JRE spec; this branch is unreachable.
            throw new IllegalStateException(e);
        }
    }

    public boolean matches(String plain, String stored) {
        return hash(plain).equals(stored);
    }
}
