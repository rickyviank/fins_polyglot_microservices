package com.finspoly.commons.audit;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

/**
 * Thin HTTP client to audit-log-service. Best-effort, never throws — auditing must not
 * block business operations. (Whether that's the right call is a design choice worth reviewing.)
 */
public class AuditClient {
    private static final Logger log = LoggerFactory.getLogger(AuditClient.class);

    private final HttpClient http;
    private final String auditServiceUrl;
    private final String service;

    public AuditClient(String auditServiceUrl, String service) {
        this.auditServiceUrl = auditServiceUrl;
        this.service = service;
        this.http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(500))
                .build();
    }

    public void emit(String actor, String action, String resourceType,
                     String resourceId, String outcome, Map<String,Object> metadata) {
        AuditEvent e = new AuditEvent(service, actor, action, resourceType, resourceId, outcome, metadata);
        try {
            String body = AuditJson.toJson(e);
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(auditServiceUrl + "/v1/events"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofMillis(500))
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();
            http.send(req, HttpResponse.BodyHandlers.discarding());
        } catch (Exception ex) {
            log.warn("audit emit failed for action={} resource={}/{}: {}",
                    action, resourceType, resourceId, ex.getMessage());
        }
    }
}
