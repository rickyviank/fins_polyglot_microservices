package com.finspoly.auth.dto;

public record TokenResponse(String accessToken, String refreshToken, long expiresInSeconds) {}
