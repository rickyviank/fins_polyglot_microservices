# transaction-service

Core money-movement service. Initiates, reads, and reverses transactions. Each successful initiation produces a double-entry posting against `ledger-service` and an audit event.

## Endpoints

| Method | Path                              | Description                                |
|--------|-----------------------------------|--------------------------------------------|
| POST   | `/v1/transactions`                | Initiate a new transaction (idempotent)    |
| GET    | `/v1/transactions/{id}`           | Fetch a transaction                        |
| GET    | `/v1/transactions?accountId=...`  | List transactions touching an account      |
| POST   | `/v1/transactions/{id}/reverse`   | Reverse a posted transaction               |

Request body (POST `/v1/transactions`):

```json
{
  "fromAccount": "1111111111",
  "toAccount":   "2222222222",
  "minorUnits":  5000,
  "currency":    "USD",
  "expectedCurrency": "USD",
  "idempotencyKey": "client-supplied-uuid"
}
```

Headers:
- `X-User-Id` — caller identity, used as audit actor.

## Run

```bash
mvn package
java -jar target/transaction-service-0.1.0.jar
```

Default port: **8081**.

## Tests

None. `mvn test` is a no-op. Test coverage is on the team backlog.

## Known limitations

- In-memory `ConcurrentHashMap` store; everything is lost on restart.
- `LedgerClient` and `FraudClient` make real HTTP calls; if those services are not reachable, transactions will fail (fraud check fails-open by design).
- No paging on `GET /v1/transactions?accountId=...` — fine for the mock dataset.
- Reversal window enforcement (`finspoly.reversal.window-hours`) is configured but not yet applied in code.
