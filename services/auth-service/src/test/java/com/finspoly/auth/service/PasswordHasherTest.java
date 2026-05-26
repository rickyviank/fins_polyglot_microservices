package com.finspoly.auth.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PasswordHasherTest {

    private PasswordHasher hasher;

    @BeforeEach
    void setUp() {
        hasher = new PasswordHasher();
    }

    @Test
    void hashProducesConsistentResults() {
        String h1 = hasher.hash("password123");
        String h2 = hasher.hash("password123");
        assertEquals(h1, h2);
    }

    @Test
    void hashProduces64CharHexString() {
        String h = hasher.hash("anything");
        assertEquals(64, h.length(), "SHA-256 hex digest should be 64 characters");
        assertTrue(h.matches("[0-9a-f]{64}"), "should be lowercase hex");
    }

    @Test
    void differentInputsProduceDifferentHashes() {
        assertNotEquals(hasher.hash("password1"), hasher.hash("password2"));
    }

    @Test
    void matchesReturnsTrueForCorrectPassword() {
        String stored = hasher.hash("secret");
        assertTrue(hasher.matches("secret", stored));
    }

    @Test
    void matchesReturnsFalseForIncorrectPassword() {
        String stored = hasher.hash("secret");
        assertFalse(hasher.matches("wrong", stored));
    }

    @Test
    void emptyPasswordCanBeHashedAndVerified() {
        String stored = hasher.hash("");
        assertTrue(hasher.matches("", stored));
        assertFalse(hasher.matches("notempty", stored));
    }
}
