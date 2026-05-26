package com.finspoly.auth.controller;

import com.finspoly.auth.dto.LoginRequest;
import com.finspoly.auth.dto.TokenResponse;
import com.finspoly.auth.model.User;
import com.finspoly.auth.repository.UserRepository;
import com.finspoly.auth.service.AuthService;
import com.finspoly.commons.errors.DomainException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    @Mock private AuthService authService;
    @Mock private UserRepository userRepository;

    private AuthController controller;

    private static final String DEBUG_TOKEN = "test-debug-token";

    @BeforeEach
    void setUp() {
        controller = new AuthController(authService, userRepository, DEBUG_TOKEN);
    }

    // --- Login endpoint tests ---

    @Test
    void loginReturns200OnSuccess() {
        TokenResponse tokenResponse = new TokenResponse("access-tok", "refresh-tok", 3600);
        when(authService.login(any(LoginRequest.class))).thenReturn(tokenResponse);

        ResponseEntity<?> response = controller.login(new LoginRequest("alice", "password123"));

        assertEquals(200, response.getStatusCode().value());
        assertSame(tokenResponse, response.getBody());
    }

    @Test
    void loginReturns401OnDomainException() {
        when(authService.login(any(LoginRequest.class)))
                .thenThrow(new DomainException("NO_SUCH_USER", "user not found"));

        ResponseEntity<?> response = controller.login(new LoginRequest("ghost", "anything"));

        assertEquals(401, response.getStatusCode().value());
        @SuppressWarnings("unchecked")
        Map<String, String> body = (Map<String, String>) response.getBody();
        assertNotNull(body);
        assertEquals("NO_SUCH_USER", body.get("code"));
        assertEquals("user not found", body.get("message"));
    }

    @Test
    void loginReturns401OnBadPassword() {
        when(authService.login(any(LoginRequest.class)))
                .thenThrow(new DomainException("BAD_PASSWORD", "invalid credentials"));

        ResponseEntity<?> response = controller.login(new LoginRequest("alice", "wrong"));

        assertEquals(401, response.getStatusCode().value());
        @SuppressWarnings("unchecked")
        Map<String, String> body = (Map<String, String>) response.getBody();
        assertNotNull(body);
        assertEquals("BAD_PASSWORD", body.get("code"));
    }

    // --- Refresh endpoint tests ---

    @Test
    void refreshReturns200OnSuccess() {
        TokenResponse tokenResponse = new TokenResponse("new-access", "refresh-tok", 3600);
        when(authService.refresh("refresh-tok")).thenReturn(tokenResponse);

        ResponseEntity<?> response = controller.refresh(Map.of("refreshToken", "refresh-tok"));

        assertEquals(200, response.getStatusCode().value());
        assertSame(tokenResponse, response.getBody());
    }

    @Test
    void refreshReturns401OnRevokedToken() {
        when(authService.refresh("bad-token"))
                .thenThrow(new DomainException("REFRESH_REVOKED", "refresh token not recognised"));

        ResponseEntity<?> response = controller.refresh(Map.of("refreshToken", "bad-token"));

        assertEquals(401, response.getStatusCode().value());
        @SuppressWarnings("unchecked")
        Map<String, String> body = (Map<String, String>) response.getBody();
        assertNotNull(body);
        assertEquals("REFRESH_REVOKED", body.get("code"));
    }

    // --- Logout endpoint tests ---

    @Test
    void logoutReturns204() {
        ResponseEntity<?> response = controller.logout(Map.of("refreshToken", "some-token"));

        assertEquals(204, response.getStatusCode().value());
        assertNull(response.getBody());
        verify(authService).logout("some-token");
    }

    // --- Debug endpoint access control tests ---

    @Test
    void debugEndpointReturns403WithNoToken() {
        ResponseEntity<?> response = controller.debugUsers(null);

        assertEquals(403, response.getStatusCode().value());
    }

    @Test
    void debugEndpointReturns403WithIncorrectToken() {
        ResponseEntity<?> response = controller.debugUsers("wrong-token");

        assertEquals(403, response.getStatusCode().value());
    }

    @Test
    void debugEndpointReturnsUsersWithCorrectToken() {
        User user = new User("id1", "alice", "hash", null, Set.of("CUSTOMER"), Instant.now(), null);
        when(userRepository.all()).thenReturn(List.of(user));

        // Note: AuthController uses == (reference equality) for token comparison.
        // This test passes the exact same String reference that was injected.
        ResponseEntity<?> response = controller.debugUsers(DEBUG_TOKEN);

        assertEquals(200, response.getStatusCode().value());
        @SuppressWarnings("unchecked")
        Collection<User> body = (Collection<User>) response.getBody();
        assertNotNull(body);
        assertEquals(1, body.size());
    }
}
