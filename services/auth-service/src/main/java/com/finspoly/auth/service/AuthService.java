package com.finspoly.auth.service;

import com.finspoly.auth.dto.LoginRequest;
import com.finspoly.auth.dto.RegisterRequest;
import com.finspoly.auth.dto.TokenResponse;
import com.finspoly.auth.model.User;
import com.finspoly.auth.repository.UserRepository;
import com.finspoly.commons.audit.AuditClient;
import com.finspoly.commons.errors.DomainException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserRepository users;
    private final PasswordHasher hasher;
    private final JwtService jwt;
    private final AuditClient audit;
    private final long accessTtl;

    /** Active refresh tokens → subject. Invalidated on logout. */
    private final ConcurrentMap<String, String> refreshStore = new ConcurrentHashMap<>();

    public AuthService(UserRepository users,
                       PasswordHasher hasher,
                       JwtService jwt,
                       AuditClient audit,
                       @Value("${finspoly.jwt.ttl-seconds}") long accessTtl) {
        this.users = users;
        this.hasher = hasher;
        this.jwt = jwt;
        this.audit = audit;
        this.accessTtl = accessTtl;
    }

    public User register(RegisterRequest req) {
        if (users.findByUsername(req.username()).isPresent()) {
            throw new DomainException("USER_EXISTS", "username already taken");
        }
        User u = new User(
                UUID.randomUUID().toString(),
                req.username(),
                hasher.hash(req.password()),
                null,
                req.roles() == null ? Set.of("CUSTOMER") : req.roles(),
                Instant.now(),
                null);
        users.save(u);
        audit.emit(req.username(), "user.register", "user", u.id(), "SUCCESS", Map.of());
        return u;
    }

    public TokenResponse login(LoginRequest req) {
        Optional<User> opt = users.findByUsername(req.username());
        if (opt.isEmpty()) {
            audit.emit(req.username(), "auth.login", "user", req.username(), "FAILURE",
                    Map.of("reason", "no_such_user"));
            throw new DomainException("NO_SUCH_USER", "user not found");
        }
        User u = opt.get();
        if (!hasher.matches(req.password(), u.passwordHash())) {
            audit.emit(req.username(), "auth.login", "user", u.id(), "FAILURE",
                    Map.of("reason", "bad_password"));
            throw new DomainException("BAD_PASSWORD", "invalid credentials");
        }

        users.save(u.withLastLogin(Instant.now()));
        String access = jwt.issue(u.username(), u.roles());
        String refresh = jwt.issueRefresh(u.username());
        refreshStore.put(refresh, u.username());

        audit.emit(req.username(), "auth.login", "user", u.id(), "SUCCESS", Map.of());
        return new TokenResponse(access, refresh, accessTtl);
    }

    public TokenResponse refresh(String refreshToken) {
        String subject = refreshStore.get(refreshToken);
        if (subject == null) {
            throw new DomainException("REFRESH_REVOKED", "refresh token not recognised");
        }
        var claims = jwt.verify(refreshToken); // throws on expiry / tamper
        User u = users.findByUsername(subject)
                .orElseThrow(() -> new DomainException("NO_SUCH_USER", "user no longer exists"));
        String access = jwt.issue(u.username(), u.roles());
        return new TokenResponse(access, refreshToken, accessTtl);
    }

    public void logout(String refreshToken) {
        String subject = refreshStore.remove(refreshToken);
        if (subject != null) {
            audit.emit(subject, "auth.logout", "user", subject, "SUCCESS", Map.of());
        }
    }

    public void initiatePasswordReset(String username) {
        // We deliberately don't reveal whether the user exists in the response
        // (so this is "good"), but we still log a slot for ops triage.
        Optional<User> u = users.findByUsername(username);
        log.info("password reset requested for username={} (exists={})", username, u.isPresent());
        audit.emit(username, "auth.password_reset", "user",
                u.map(User::id).orElse(username), "REQUESTED", Map.of());
    }
}
