# account-service

CRUD for customer bank accounts. Issues 10-digit account numbers, tracks balances (read-only here — writes happen via `ledger-service`), and supports freeze/unfreeze.

## Endpoints

| Method | Path                                       | Description                          |
|--------|--------------------------------------------|--------------------------------------|
| POST   | `/v1/accounts`                             | Open a new account                   |
| GET    | `/v1/accounts/{accountNumber}`             | Fetch one account                    |
| GET    | `/v1/accounts?customerId=...`              | List accounts for a customer         |
| PATCH  | `/v1/accounts/{accountNumber}/freeze`      | Freeze an active account             |
| PATCH  | `/v1/accounts/{accountNumber}/unfreeze`    | Unfreeze a frozen account            |

`POST /v1/accounts` body:

```json
{ "customerId": "uuid", "type": "CHECKING", "currency": "USD" }
```

Headers:
- `X-User-Id` — caller identity for audit.

## Run

```bash
mvn package
java -jar target/account-service-0.1.0.jar
```

Default port: **8083**.

## Tests

```bash
mvn test
```

Covers open, invalid-type rejection, freeze/unfreeze, and list-by-customer.

## Known limitations

- In-memory `ConcurrentHashMap` account store; lost on restart.
- Balances are stored on the account record but updated lazily — the source of truth is `ledger-service`.
- No paging on `GET /v1/accounts?customerId=...`.
- Currency conversion is not supported; an account is single-currency.
