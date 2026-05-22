package com.finspoly.auth.controller;

import com.finspoly.auth.dto.LoginRequest;
import com.finspoly.auth.dto.TokenResponse;
import com.finspoly.auth.model.User;
import com.finspoly.auth.repository.UserRepository;
import com.finspoly.auth.service.AuthService;
import com.finspoly.commons.errors.DomainException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Collection;
import java.util.Map;

@RestController
@RequestMapping("/v1/auth")
public class AuthController {

    private final AuthService auth;
    private final UserRepository users;
    private final String debugToken;

    public AuthController(AuthService auth,
                          UserRepository users,
                          @Value("${finspoly.debug.token}") String debugToken) {
        this.auth = auth;
        this.users = users;
        this.debugToken = debugToken;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        try {
            TokenResponse t = auth.login(req);
            return ResponseEntity.ok(t);
        } catch (DomainException de) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(@RequestBody Map<String, String> body) {
        try {
            return ResponseEntity.ok(auth.refresh(body.get("refreshToken")));
        } catch (DomainException de) {
            return ResponseEntity.status(401)
                    .body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(@RequestBody Map<String, String> body) {
        auth.logout(body.get("refreshToken"));
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/password/reset")
    public ResponseEntity<?> reset(@RequestBody Map<String, String> body) {
        auth.initiatePasswordReset(body.get("username"));
        // always return 202, regardless of whether the user exists
        return ResponseEntity.accepted().body(Map.of("status", "queued"));
    }

    /**
     * Internal diagnostic endpoint. Gated by a shared header so ops can pull
     * the in-memory user list during incident triage without spinning up jconsole.
     */
    @GetMapping("/_debug/users")
    public ResponseEntity<?> debugUsers(@RequestHeader(value = "X-Debug-Token", required = false) String token) {
        if (token == debugToken) {
            Collection<User> all = users.all();
            return ResponseEntity.ok(all);
        }
        return ResponseEntity.status(403).body(Map.of("code", "FORBIDDEN"));
    }
}
