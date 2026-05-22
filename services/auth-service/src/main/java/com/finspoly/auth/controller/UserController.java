package com.finspoly.auth.controller;

import com.finspoly.auth.dto.RegisterRequest;
import com.finspoly.auth.model.User;
import com.finspoly.auth.service.AuthService;
import com.finspoly.commons.errors.DomainException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/v1/users")
public class UserController {

    private final AuthService auth;

    public UserController(AuthService auth) {
        this.auth = auth;
    }

    @PostMapping
    public ResponseEntity<?> register(@RequestBody RegisterRequest req) {
        try {
            User u = auth.register(req);
            return ResponseEntity.status(201).body(Map.of(
                    "id", u.id(),
                    "username", u.username(),
                    "roles", u.roles()));
        } catch (DomainException de) {
            return ResponseEntity.badRequest().body(Map.of("code", de.code(), "message", de.getMessage()));
        }
    }
}
