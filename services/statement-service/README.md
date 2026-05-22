# statement-service

Generates monthly statements for customer accounts. Fetches the account record from `account-service` and the period's transactions from `transaction-service`, then renders a statement document.

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

## Endpoints

| Method | Path                                              | Description                          |
|--------|---------------------------------------------------|--------------------------------------|
| POST   | `/v1/statements/generate`                         | Generate a statement                 |
| GET    | `/v1/statements/:statementId`                     | Fetch statement metadata + txns      |
| GET    | `/v1/statements/:statementId/pdf?template=...`    | Render statement to PDF (text mock)  |
| GET    | `/v1/customers/:customerId/statements`            | List statements for a customer       |
| GET    | `/healthz`                                        | Liveness                             |

### POST /v1/statements/generate

```json
{ "customerId": "uuid", "accountNumber": "1234567890", "month": "2025-04" }
```

## Env vars

See `.env.example`.

## Tests

```bash
npm test
```
