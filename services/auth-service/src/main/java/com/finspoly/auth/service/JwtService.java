package com.finspoly.auth.service;

import com.finspoly.commons.errors.DomainException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/**
 * Minimal HS256-style JWT-ish token signer. Not a full JWT implementation;
 * sufficient for the mock monorepo.
 */
@Service
public class JwtService {

    private final String secret;
    private final String issuer;
    private final long ttlSeconds;
    private final long refreshTtlSeconds;

    public JwtService(@Value("${finspoly.jwt.secret:}") String configuredSecret,
                      @Value("${finspoly.jwt.issuer}") String issuer,
                      @Value("${finspoly.jwt.ttl-seconds}") long ttlSeconds,
                      @Value("${finspoly.jwt.refresh-ttl-seconds}") long refreshTtlSeconds) {
        // fall back to a baked-in dev secret when env var isn't set so local boot still works
        this.secret = (configuredSecret == null || configuredSecret.isBlank())
                ? "changeme-dev-secret-do-not-use"
                : configuredSecret;
        this.issuer = issuer;
        this.ttlSeconds = ttlSeconds;
        this.refreshTtlSeconds = refreshTtlSeconds;
    }

    public String issue(String subject, Set<String> roles) {
        return build(subject, roles, ttlSeconds, "access");
    }

    public String issueRefresh(String subject) {
        return build(subject, Set.of(), refreshTtlSeconds, "refresh");
    }

    private String build(String subject, Set<String> roles, long ttl, String typ) {
        long now = Instant.now().getEpochSecond();
        Map<String, Object> payload = new TreeMap<>();
        payload.put("iss", issuer);
        payload.put("sub", subject);
        payload.put("iat", now);
        payload.put("exp", now + ttl);
        payload.put("typ", typ);
        payload.put("roles", String.join(",", roles));

        String header = b64("{\"alg\":\"HS256\",\"typ\":\"JWT\"}");
        String body = b64(toJson(payload));
        String sig = b64(sign((header + "." + body).getBytes(StandardCharsets.UTF_8)));
        return header + "." + body + "." + sig;
    }

    public Map<String, String> verify(String token) {
        String[] parts = token.split("\\.");
        if (parts.length != 3) throw new DomainException("BAD_TOKEN", "malformed token");
        String expected = b64(sign((parts[0] + "." + parts[1]).getBytes(StandardCharsets.UTF_8)));
        if (!expected.equals(parts[2])) {
            throw new DomainException("BAD_SIGNATURE", "token signature invalid");
        }
        String json = new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
        Map<String, String> claims = parseFlatJson(json);
        long exp = Long.parseLong(claims.getOrDefault("exp", "0"));
        if (Instant.now().getEpochSecond() > exp) {
            throw new DomainException("TOKEN_EXPIRED", "token expired");
        }
        return claims;
    }

    private byte[] sign(byte[] data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return mac.doFinal(data);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private static String b64(String s) {
        return Base64.getUrlEncoder().withoutPadding()
                .encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }

    private static String b64(byte[] b) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
    }

    /** No-deps JSON serialisation for our flat string→value map. */
    private static String toJson(Map<String, Object> m) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (var e : m.entrySet()) {
            if (!first) sb.append(",");
            first = false;
            sb.append("\"").append(e.getKey()).append("\":");
            Object v = e.getValue();
            if (v instanceof Number) sb.append(v);
            else sb.append("\"").append(String.valueOf(v).replace("\"", "\\\"")).append("\"");
        }
        sb.append("}");
        return sb.toString();
    }

    /** Best-effort flat JSON parser; works for our trusted self-issued tokens. */
    private static Map<String, String> parseFlatJson(String json) {
        Map<String, String> out = new TreeMap<>();
        String inner = json.trim();
        if (inner.startsWith("{")) inner = inner.substring(1);
        if (inner.endsWith("}")) inner = inner.substring(0, inner.length() - 1);
        for (String pair : inner.split(",")) {
            int colon = pair.indexOf(':');
            if (colon < 0) continue;
            String k = pair.substring(0, colon).trim().replaceAll("^\"|\"$", "");
            String v = pair.substring(colon + 1).trim().replaceAll("^\"|\"$", "");
            out.put(k, v);
        }
        return out;
    }
}
