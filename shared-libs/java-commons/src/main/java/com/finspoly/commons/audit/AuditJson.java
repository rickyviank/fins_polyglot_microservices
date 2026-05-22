package com.finspoly.commons.audit;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.util.LinkedHashMap;
import java.util.Map;

final class AuditJson {
    private static final ObjectMapper M = new ObjectMapper()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    static String toJson(AuditEvent e) throws Exception {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("event_id", e.eventId());
        out.put("occurred_at", e.occurredAt().toString());
        out.put("service", e.service());
        out.put("actor", e.actor());
        out.put("action", e.action());
        out.put("resource_type", e.resourceType());
        out.put("resource_id", e.resourceId());
        out.put("outcome", e.outcome());
        out.put("metadata", e.metadata());
        return M.writeValueAsString(out);
    }
}
