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
 * Thin client for ledger-service. Posts a double-entry record on each transaction.
 */
@Component
public class LedgerClient {
    private static final Logger log = LoggerFactory.getLogger(LedgerClient.class);

    private final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(1)).build();
    private final String baseUrl;

    public LedgerClient(@Value("${finspoly.ledger.url}") String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public boolean postDoubleEntry(String txnId, String from, String to, long minorUnits, String currency) {
        String body = String.format(
                "{\"debitAccountId\":\"%s\",\"creditAccountId\":\"%s\",\"minorUnits\":%d,\"currency\":\"%s\",\"narrative\":\"txn:%s\"}",
                from, to, minorUnits, currency, txnId);
        try {
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/v1/postings"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(2))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            return res.statusCode() >= 200 && res.statusCode() < 300;
        } catch (Exception e) {
            log.warn("ledger post failed for txn {}: {}", txnId, e.getMessage());
            return false;
        }
    }
}
