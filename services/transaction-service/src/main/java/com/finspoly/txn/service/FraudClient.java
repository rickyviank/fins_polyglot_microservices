package com.finspoly.txn.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * Calls fraud-detection-service for a score. Returns true if the txn is
 * allowed, false if blocked. Fails-open on network errors (deliberate).
 */
@Component
public class FraudClient {
    private static final Logger log = LoggerFactory.getLogger(FraudClient.class);

    private final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(1)).build();
    private final String baseUrl;

    public FraudClient(@Value("${finspoly.fraud.url}") String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public boolean allow(String fromAccount, String toAccount, long minorUnits) {
        String body = String.format(
                "{\"fromAccount\":\"%s\",\"toAccount\":\"%s\",\"minorUnits\":%d}",
                fromAccount, toAccount, minorUnits);
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/v1/score"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofMillis(800))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            // crude parse: assume body contains "block":true or "block":false
            return !res.body().contains("\"block\":true");
        } catch (Exception e) {
            log.warn("fraud check failed, failing open: {}", e.getMessage());
            return true;
        }
    }
}
