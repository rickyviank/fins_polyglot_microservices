# ledger-service

Append-only double-entry ledger. Records debit/credit pairs and computes per-account balances by replay.

## Endpoints

| Method | Path                                       | Description                          |
|--------|--------------------------------------------|--------------------------------------|
| POST   | `/v1/postings`                             | Record a debit + credit pair         |
| GET    | `/v1/postings/{id}`                        | Fetch a single posting               |
| GET    | `/v1/accounts/{accountId}/entries`         | List per-account ledger entries      |
| GET    | `/v1/accounts/{accountId}/balance`         | Computed balance for an account      |

`POST /v1/postings` body:

```json
{
  "debitAccountId":  "1111111111",
  "creditAccountId": "2222222222",
  "minorUnits": 5000,
  "currency": "USD",
  "narrative": "txn:01HXYZ..."
}
```

## Run

```bash
mvn package
java -jar target/ledger-service-0.1.0.jar
```

Default port: **8084**.

## Tests

```bash
mvn test
```

Only a context-load smoke test is wired up. Unit coverage of the posting logic is on the backlog — this is one of the lower-priority services from a delivery perspective.

## Known limitations

- In-memory store; everything is lost on restart.
- Single-currency balance computation. A posting that mixes currencies will produce undefined behaviour.
- No paging on `GET /v1/accounts/{accountId}/entries`.
- Intended as an **internal** service. Reached only via other backend services on the private network.
