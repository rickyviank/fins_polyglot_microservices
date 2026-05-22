# auth-service

Issues and verifies JWT-style access/refresh tokens, registers users, and handles password-reset initiation. In-memory user store.

## Endpoints

| Method | Path                          | Description                                |
|--------|-------------------------------|--------------------------------------------|
| POST   | `/v1/auth/login`              | Username/password → access + refresh tokens |
| POST   | `/v1/auth/refresh`            | Refresh token → new access token            |
| POST   | `/v1/auth/logout`             | Invalidate a refresh token                  |
| POST   | `/v1/auth/password/reset`     | Initiate a password reset                   |
| POST   | `/v1/users`                   | Register a new user                         |

`POST /v1/auth/login` request body:

```json
{ "username": "alice", "password": "hunter2" }
```

## Config

| Key                              | Description                                  |
|----------------------------------|----------------------------------------------|
| `finspoly.jwt.secret`            | HMAC secret (loaded from env `JWT_SECRET`)   |
| `finspoly.jwt.issuer`            | `iss` claim                                  |
| `finspoly.jwt.ttl-seconds`       | Access token TTL                             |
| `finspoly.jwt.refresh-ttl-seconds` | Refresh token TTL                          |

## Run

```bash
mvn package
JWT_SECRET=$(openssl rand -hex 32) java -jar target/auth-service-0.1.0.jar
```

Default port: **8082**.

## Tests

None. Test scaffolding has not been prioritised — see [`backlog/AUTH-tests.md`](#) (not present in repo). `mvn test` is a no-op for this module.

## Known limitations

- In-memory `ConcurrentHashMap` user store; lost on restart.
- No rate-limiting on `/v1/auth/login` — relies on `api-gateway` in production.
- Password reset only emits an audit event; it does not yet send email (depends on `notification-service`).
- Refresh tokens are tracked in-process; multi-instance deployments would need Redis or similar.
