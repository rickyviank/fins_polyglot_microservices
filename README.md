# fins-polyglot-microservices

A polyglot mock monorepo modeling a mid-sized retail bank's backend. 12 microservices across Java, TypeScript, and Python, plus 3 shared libraries.

> **NOTE:** This is a **mock codebase** intended for code review training, static analysis tooling evaluation, and architecture reference. Services run with in-memory stores and stubbed inter-service calls. **Do not deploy this anywhere.** Some files intentionally contain realistic security weaknesses that you'd find in production fin-services code (PII in logs, weak crypto, SQL injection, IDOR, hardcoded secrets, etc.) — they are review fodder, not best-practice examples.

## Layout

```
fins_polyglot_microservices/
├── services/
│   ├── transaction-service/        (Java / Spring Boot)   — core payment processing
│   ├── auth-service/               (Java / Spring Boot)   — login, JWT issuance, password mgmt
│   ├── account-service/            (Java / Spring Boot)   — account CRUD, balance read
│   ├── ledger-service/             (Java / Spring Boot)   — double-entry ledger, postings
│   ├── api-gateway/                (TypeScript / Express) — edge routing, rate limit, auth fwd
│   ├── notification-service/       (TypeScript / Node)    — email / SMS / push fanout
│   ├── customer-profile-service/   (TypeScript / Node)    — customer master + PII
│   ├── statement-service/          (TypeScript / Node)    — monthly statement generation
│   ├── fraud-detection-service/    (Python / FastAPI)     — rule + ML scoring of txns
│   ├── audit-log-service/          (Python / FastAPI)     — append-only audit trail
│   ├── kyc-service/                (Python / FastAPI)     — identity verification, sanctions
│   └── reporting-service/          (Python / FastAPI)     — regulatory + ops reporting
└── shared-libs/
    ├── java-commons/    — money type, validators, audit client (Java)
    ├── ts-commons/      — error types, schemas, audit client (TS)
    └── py-commons/      — money, validators, audit client (Python)
```

## Build / run

Each service is independent. No root build system, no Docker Compose, no orchestrator.

| Stack       | Build / run                              |
|-------------|-------------------------------------------|
| Java        | `cd services/<svc> && mvn package && java -jar target/*.jar` |
| TypeScript  | `cd services/<svc> && npm install && npm run dev`           |
| Python      | `cd services/<svc> && pip install -e . && uvicorn app.main:app` |

Tests:

| Stack       | Test command          |
|-------------|------------------------|
| Java        | `mvn test`             |
| TypeScript  | `npm test`             |
| Python      | `pytest`               |

Approximate aggregate test coverage: **very low (~5%)**. The codebase is intentionally sparsely tested — common in fast-moving fin-services teams that prioritise feature delivery over test investment.

- **Zero tests** (critical path included): `transaction-service`, `auth-service`, `customer-profile-service`, `audit-log-service`, `ledger-service`, `notification-service`, `reporting-service`.
- **One token test** (smoke/regression only): `account-service`, `api-gateway`, `fraud-detection-service`, `kyc-service`, `statement-service`.
- Shared libs have minimal `Money` arithmetic tests only.

This shape — critical code untested, peripheral code lightly tested — is itself a finding worth flagging in any code review.

## CI

GitHub Actions workflows live in `.github/workflows/`:

- `java.yml` — matrix build over the 4 Java services; uses Temurin 17, caches Maven.
- `typescript.yml` — matrix build over the 4 Node services; uses Node 20, caches npm.
- `python.yml` — matrix build over the 4 Python services; uses Python 3.11, caches pip.
- `shared-libs.yml` — builds/installs the three shared libraries (prerequisite for the per-service jobs).

Each per-language workflow is gated by path filters so unrelated changes don't trigger unnecessary jobs.

## Topology (conceptual)

```
                                  ┌──────────────┐
        client ────HTTPS────►     │ api-gateway  │
                                  └──────┬───────┘
                                         │
        ┌───────────────┬────────────────┼────────────────┬──────────────┐
        ▼               ▼                ▼                ▼              ▼
   auth-service   customer-profile  transaction-svc   statement-svc   kyc-service
        │               │                │                │              │
        │               │                ├──► fraud-detection            │
        │               │                ├──► ledger-service             │
        └───────────────┴────────────────┴───► audit-log-service ◄───────┘
                                                                        ▲
                                                  reporting-service ────┘
                                                  notification-service ─┘
```

## Domain notes

- **Currency**: all monetary values use minor units (cents) — never floats. See `shared-libs/*/Money`.
- **Identifiers**: customer IDs are UUIDs; account numbers are 10-digit strings; transaction IDs are ULIDs.
- **Time**: all timestamps are UTC, ISO-8601 with millisecond precision.
- **PII scope**: name, DOB, government ID (SSN/TIN), full address, phone, email, account number.

## What's intentionally NOT here

- Real persistence (Postgres, etc.) — repos are in-memory `HashMap`/`dict`/`Map<string,…>`.
- Real auth provider integration (Okta/Auth0/Cognito) — JWTs are signed locally.
- Real message bus (Kafka/RabbitMQ) — async work is fire-and-forget or synchronous.
- CI/CD, IaC, Helm charts, observability stack.
