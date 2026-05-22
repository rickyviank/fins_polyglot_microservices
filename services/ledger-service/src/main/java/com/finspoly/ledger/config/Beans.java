package com.finspoly.ledger.config;

import com.finspoly.commons.audit.AuditClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class Beans {

    @Bean
    public AuditClient auditClient(@Value("${finspoly.audit.url}") String url) {
        return new AuditClient(url, "ledger-service");
    }
}
