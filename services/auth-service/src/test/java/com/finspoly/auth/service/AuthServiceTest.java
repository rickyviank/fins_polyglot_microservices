package com.finspoly.auth.service;

import com.finspoly.auth.dto.LoginRequest;
import com.finspoly.auth.dto.TokenResponse;
import com.finspoly.auth.model.User;
import com.finspoly.auth.repository.UserRepository;
import com.finspoly.commons.audit.AuditClient;
import com.finspoly.commons.errors.DomainException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock private UserRepository users;
    @Mock private AuditClient audit;

    private PasswordHasher hasher;
    private JwtService jwt;
    private AuthService authService;

    private static final long ACCESS_TTL = 3600;

    @BeforeEach
    void setUp() {
        hasher = new PasswordHasher();
        jwt = new JwtService("test-secret", "finspoly-auth-test", ACCESS_TTL, 86400);
        authService = new AuthService(users, hasher, jwt, audit, ACCESS_TTL);
    }

    private User testUser(String username, String password) {
        return new User(
                "user-123",
                username,
                hasher.hash(password),
                null,
                Set.of("CUSTOMER"),
                Instant.now(),
                null
        );
    }

    // --- Login tests ---

    @Test
    void loginWithValidCredentialsReturnsTokens() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        TokenResponse response = authService.login(new LoginRequest("alice", "password123"));

        assertNotNull(response.accessToken());
        assertNotNull(response.refreshToken());
        assertEquals(ACCESS_TTL, response.expiresInSeconds());

        Map<String, String> claims = jwt.verify(response.accessToken());
        assertEquals("alice", claims.get("sub"));
        assertEquals("access", claims.get("typ"));
    }

    @Test
    void loginUpdatesLastLoginTimestamp() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        authService.login(new LoginRequest("alice", "password123"));

        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(users, times(1)).save(captor.capture());
        assertNotNull(captor.getValue().lastLoginAt());
    }

    @Test
    void loginFailureForNonExistentUser() {
        when(users.findByUsername("ghost")).thenReturn(Optional.empty());

        DomainException ex = assertThrows(DomainException.class,
                () -> authService.login(new LoginRequest("ghost", "anything")));
        assertEquals("NO_SUCH_USER", ex.code());
    }

    @Test
    void loginFailureForIncorrectPassword() {
        User user = testUser("alice", "correctPassword");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        DomainException ex = assertThrows(DomainException.class,
                () -> authService.login(new LoginRequest("alice", "wrongPassword")));
        assertEquals("BAD_PASSWORD", ex.code());
    }

    // --- Audit event tests ---

    @Test
    void loginSuccessEmitsAuditEvent() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        authService.login(new LoginRequest("alice", "password123"));

        verify(audit).emit(
                eq("alice"),
                eq("auth.login"),
                eq("user"),
                eq("user-123"),
                eq("SUCCESS"),
                eq(Map.of())
        );
    }

    @Test
    void loginFailureForNonExistentUserEmitsAuditEvent() {
        when(users.findByUsername("ghost")).thenReturn(Optional.empty());

        assertThrows(DomainException.class,
                () -> authService.login(new LoginRequest("ghost", "anything")));

        verify(audit).emit(
                eq("ghost"),
                eq("auth.login"),
                eq("user"),
                eq("ghost"),
                eq("FAILURE"),
                eq(Map.of("reason", "no_such_user"))
        );
    }

    @Test
    void loginFailureForBadPasswordEmitsAuditEvent() {
        User user = testUser("alice", "correct");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        assertThrows(DomainException.class,
                () -> authService.login(new LoginRequest("alice", "wrong")));

        verify(audit).emit(
                eq("alice"),
                eq("auth.login"),
                eq("user"),
                eq("user-123"),
                eq("FAILURE"),
                eq(Map.of("reason", "bad_password"))
        );
    }

    // --- Refresh token tests ---

    @Test
    void refreshWithValidTokenReturnsNewAccessToken() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        TokenResponse loginResponse = authService.login(new LoginRequest("alice", "password123"));

        TokenResponse refreshResponse = authService.refresh(loginResponse.refreshToken());

        assertNotNull(refreshResponse.accessToken());
        // Verify the new access token is valid
        Map<String, String> claims = jwt.verify(refreshResponse.accessToken());
        assertEquals("alice", claims.get("sub"));
        assertEquals("access", claims.get("typ"));
        // Refresh token is reused
        assertEquals(loginResponse.refreshToken(), refreshResponse.refreshToken());
        assertEquals(ACCESS_TTL, refreshResponse.expiresInSeconds());
    }

    @Test
    void refreshFailsForUnknownToken() {
        DomainException ex = assertThrows(DomainException.class,
                () -> authService.refresh("unknown-refresh-token"));
        assertEquals("REFRESH_REVOKED", ex.code());
    }

    @Test
    void refreshFailsAfterLogout() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        TokenResponse loginResponse = authService.login(new LoginRequest("alice", "password123"));
        authService.logout(loginResponse.refreshToken());

        DomainException ex = assertThrows(DomainException.class,
                () -> authService.refresh(loginResponse.refreshToken()));
        assertEquals("REFRESH_REVOKED", ex.code());
    }

    @Test
    void refreshFailsWhenUserNoLongerExists() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice"))
                .thenReturn(Optional.of(user))   // for login
                .thenReturn(Optional.empty());     // for refresh

        TokenResponse loginResponse = authService.login(new LoginRequest("alice", "password123"));

        DomainException ex = assertThrows(DomainException.class,
                () -> authService.refresh(loginResponse.refreshToken()));
        assertEquals("NO_SUCH_USER", ex.code());
    }

    // --- Logout tests ---

    @Test
    void logoutRevokesRefreshToken() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        TokenResponse loginResponse = authService.login(new LoginRequest("alice", "password123"));
        authService.logout(loginResponse.refreshToken());

        verify(audit).emit(
                eq("alice"),
                eq("auth.logout"),
                eq("user"),
                eq("alice"),
                eq("SUCCESS"),
                eq(Map.of())
        );
    }

    @Test
    void logoutWithUnknownTokenDoesNotEmitAudit() {
        authService.logout("unknown-token");

        verify(audit, never()).emit(anyString(), eq("auth.logout"),
                anyString(), anyString(), anyString(), any());
    }

    @Test
    void doubleLogoutSecondCallDoesNotEmitAudit() {
        User user = testUser("alice", "password123");
        when(users.findByUsername("alice")).thenReturn(Optional.of(user));

        TokenResponse loginResponse = authService.login(new LoginRequest("alice", "password123"));
        authService.logout(loginResponse.refreshToken());
        authService.logout(loginResponse.refreshToken());

        verify(audit, times(1)).emit(
                eq("alice"),
                eq("auth.logout"),
                eq("user"),
                eq("alice"),
                eq("SUCCESS"),
                eq(Map.of())
        );
    }
}
