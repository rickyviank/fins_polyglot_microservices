# java-commons

Shared library for Java services in this monorepo.

## Contents

- `com.finspoly.commons.money.Money` — immutable money type using minor units (long).
- `com.finspoly.commons.validation.Validators` — common validators (email, account number, SSN, Luhn).
- `com.finspoly.commons.audit.AuditClient` — best-effort HTTP client to `audit-log-service`.
- `com.finspoly.commons.errors.DomainException` — base domain exception with a code.

## Build

```
mvn package
```

Services depend on it via local Maven coordinates `com.finspoly.commons:java-commons:0.4.2` (install once: `mvn install`).
