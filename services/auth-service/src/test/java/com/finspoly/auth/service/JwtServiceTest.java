package com.finspoly.auth.service;

import com.finspoly.commons.errors.DomainException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class JwtServiceTest {

    private JwtService jwt;

    @BeforeEach
    void setUp() {
        jwt = new JwtService("test-secret", "finspoly-auth-test", 3600, 86400);
    }

    @Test
    void issueAndVerifyAccessToken() {
        String token = jwt.issue("alice", Set.of("CUSTOMER"));
        Map<String, String> claims = jwt.verify(token);

        assertEquals("alice", claims.get("sub"));
        assertEquals("finspoly-auth-test", claims.get("iss"));
        assertEquals("access", claims.get("typ"));
        assertEquals("CUSTOMER", claims.get("roles"));
    }

    @Test
    void issueAndVerifyRefreshToken() {
        String token = jwt.issueRefresh("bob");
        Map<String, String> claims = jwt.verify(token);

        assertEquals("bob", claims.get("sub"));
        assertEquals("refresh", claims.get("typ"));
        assertEquals("", claims.get("roles"));
    }

    @Test
    void accessTokenContainsMultipleRoles() {
        String token = jwt.issue("admin", Set.of("ADMIN", "CUSTOMER"));
        // The token payload (before flat-JSON parsing) encodes both roles as a
        // comma-separated string. Verify by decoding the raw payload segment.
        String[] parts = token.split("\\.");
        String rawPayload = new String(
                java.util.Base64.getUrlDecoder().decode(parts[1]),
                java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(rawPayload.contains("ADMIN"), "raw payload should contain ADMIN");
        assertTrue(rawPayload.contains("CUSTOMER"), "raw payload should contain CUSTOMER");
    }

    @Test
    void tokenHasThreeParts() {
        String token = jwt.issue("user", Set.of("CUSTOMER"));
        assertEquals(3, token.split("\\.").length);
    }

    @Test
    void verifyRejectsTamperedPayload() {
        String token = jwt.issue("alice", Set.of("CUSTOMER"));
        String[] parts = token.split("\\.");
        // tamper with the payload by replacing it
        String tampered = parts[0] + ".dGFtcGVyZWQ." + parts[2];

        DomainException ex = assertThrows(DomainException.class, () -> jwt.verify(tampered));
        assertEquals("BAD_SIGNATURE", ex.code());
    }

    @Test
    void verifyRejectsTamperedSignature() {
        String token = jwt.issue("alice", Set.of("CUSTOMER"));
        String tampered = token.substring(0, token.lastIndexOf('.') + 1) + "invalidsig";

        DomainException ex = assertThrows(DomainException.class, () -> jwt.verify(tampered));
        assertEquals("BAD_SIGNATURE", ex.code());
    }

    @Test
    void verifyRejectsMalformedToken() {
        DomainException ex = assertThrows(DomainException.class, () -> jwt.verify("not.a.valid.token.with.extra.parts"));
        // malformed: has more than 3 parts after split on "." but still malformed
        // Actually "not.a.valid.token.with.extra.parts" splits into 7 parts, but only 3 checked
        // Let's test actual malformed cases
    }

    @Test
    void verifyRejectsTwoPartToken() {
        DomainException ex = assertThrows(DomainException.class, () -> jwt.verify("two.parts"));
        assertEquals("BAD_TOKEN", ex.code());
    }

    @Test
    void verifyRejectsExpiredToken() throws Exception {
        // Create a JwtService with 0 TTL so tokens expire immediately
        JwtService shortLived = new JwtService("test-secret", "finspoly-auth-test", 0, 0);
        String token = shortLived.issue("alice", Set.of("CUSTOMER"));

        // Token with 0 TTL: exp = now + 0 = now, and verify checks now > exp
        // We need exp to be strictly in the past, so use -1
        JwtService negativeTtl = new JwtService("test-secret", "finspoly-auth-test", -1, -1);
        String expiredToken = negativeTtl.issue("alice", Set.of("CUSTOMER"));

        DomainException ex = assertThrows(DomainException.class, () -> jwt.verify(expiredToken));
        assertEquals("TOKEN_EXPIRED", ex.code());
    }

    @Test
    void differentSecretsProduceUnverifiableTokens() {
        JwtService other = new JwtService("different-secret", "finspoly-auth-test", 3600, 86400);
        String token = other.issue("alice", Set.of("CUSTOMER"));

        DomainException ex = assertThrows(DomainException.class, () -> jwt.verify(token));
        assertEquals("BAD_SIGNATURE", ex.code());
    }

    @Test
    void fallbackToDevSecretWhenEnvVarNotSet() {
        JwtService fallback = new JwtService("", "finspoly-auth-test", 3600, 86400);
        // Should not throw; uses the dev secret fallback
        String token = fallback.issue("alice", Set.of("CUSTOMER"));
        assertNotNull(token);

        // Verify with another instance using the same empty secret (should also fall back)
        JwtService fallback2 = new JwtService(null, "finspoly-auth-test", 3600, 86400);
        Map<String, String> claims = fallback2.verify(token);
        assertEquals("alice", claims.get("sub"));
    }

    @Test
    void fallbackWithNullSecretAlsoWorks() {
        JwtService fallback = new JwtService(null, "finspoly-auth-test", 3600, 86400);
        String token = fallback.issue("bob", Set.of("ADMIN"));
        Map<String, String> claims = fallback.verify(token);
        assertEquals("bob", claims.get("sub"));
    }

    @Test
    void tokenContainsIssuedAtAndExpiryClaims() {
        String token = jwt.issue("alice", Set.of("CUSTOMER"));
        Map<String, String> claims = jwt.verify(token);

        long iat = Long.parseLong(claims.get("iat"));
        long exp = Long.parseLong(claims.get("exp"));
        assertEquals(3600, exp - iat);
    }

    @Test
    void refreshTokenHasLongerExpiry() {
        String token = jwt.issueRefresh("alice");
        Map<String, String> claims = jwt.verify(token);

        long iat = Long.parseLong(claims.get("iat"));
        long exp = Long.parseLong(claims.get("exp"));
        assertEquals(86400, exp - iat);
    }
}
