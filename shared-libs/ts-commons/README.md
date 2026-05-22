# @finspoly/ts-commons

Shared TypeScript utilities for fins-polyglot Node services.

## Contents

- `money` — Money type and arithmetic helpers (minor-unit integers).
- `validation/validators` — email, account number, SSN, Luhn.
- `audit/auditClient` — best-effort fetch client to `audit-log-service`.
- `errors/domainError` — `DomainError`, `ValidationError`, `NotFoundError`, `UnauthorizedError`.
- `schemas/common` — shared Zod schemas (CustomerId, AccountNumber, Money, PageQuery).

## Build / test

```
npm install
npm run build
npm test
```

Services depend on it via a local file path (`"file:../../shared-libs/ts-commons"` in their `package.json`).
