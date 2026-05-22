# api-gateway

Edge router for the fins-polyglot platform. Forwards requests to upstream services, enforces a token-bucket rate limit per IP, injects a per-request correlation id, and decodes the bearer JWT for downstream services.

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

## Endpoints

The gateway proxies based on path prefix:

| Prefix         | Upstream                |
|----------------|--------------------------|
| `/auth/*`      | `AUTH_SERVICE_URL`       |
| `/accounts/*`  | `ACCOUNT_SERVICE_URL`    |
| `/txns/*`      | `TXN_SERVICE_URL`        |
| `/customers/*` | `CUSTOMER_SERVICE_URL`   |
| `/statements/*`| `STATEMENT_SERVICE_URL`  |

Additional:

- `GET /healthz` — liveness probe.
- `GET /readyz`  — readiness probe.

## Env vars

See `.env.example`. All upstream URLs are required; the gateway will start without them but every forwarded request will 502.

## Tests

```bash
npm test
```
