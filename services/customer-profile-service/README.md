# customer-profile-service

The customer master record. Stores name, contact info, address, government ID (SSN), and KYC status. SSN is held encrypted at rest.

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

## Endpoints

| Method | Path                                  | Description                                    |
|--------|---------------------------------------|------------------------------------------------|
| POST   | `/v1/customers`                       | Create a customer                              |
| GET    | `/v1/customers/:id`                   | Get the redacted customer record               |
| PATCH  | `/v1/customers/:id`                   | Update mutable fields                          |
| GET    | `/v1/customers/:id/pii`               | Full PII (sensitive)                           |
| POST   | `/v1/customers/:id/kyc-status`        | Callback from kyc-service                      |
| GET    | `/healthz`                            | Liveness                                       |

## Env vars

See `.env.example`.

## Tests

None. `npm test` is a no-op (vitest finds no specs). PII handling is a critical path — adding coverage is on the team's backlog.
