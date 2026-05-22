package com.finspoly.commons.audit;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public final class AuditEvent {
    private final String eventId;
    private final Instant occurredAt;
    private final String service;
    private final String actor;
    private final String action;
    private final String resourceType;
    private final String resourceId;
    private final String outcome;
    private final Map<String, Object> metadata;

    public AuditEvent(String service, String actor, String action,
                      String resourceType, String resourceId, String outcome,
                      Map<String, Object> metadata) {
        this.eventId = UUID.randomUUID().toString();
        this.occurredAt = Instant.now();
        this.service = service;
        this.actor = actor;
        this.action = action;
        this.resourceType = resourceType;
        this.resourceId = resourceId;
        this.outcome = outcome;
        this.metadata = metadata;
    }

    public String eventId()          { return eventId; }
    public Instant occurredAt()      { return occurredAt; }
    public String service()          { return service; }
    public String actor()            { return actor; }
    public String action()           { return action; }
    public String resourceType()     { return resourceType; }
    public String resourceId()       { return resourceId; }
    public String outcome()          { return outcome; }
    public Map<String,Object> metadata() { return metadata; }
}
