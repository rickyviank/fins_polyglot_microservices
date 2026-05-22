# notification-service

Fan-out service for transactional notifications. Accepts email / SMS / push requests, renders a template, enqueues to an in-memory queue, and dispatches via a (stubbed) provider.

## Run

```bash
npm install
cp .env.example .env
npm run dev
```

## Endpoints

| Method | Path                          | Body                                                  |
|--------|-------------------------------|-------------------------------------------------------|
| POST   | `/v1/notifications/email`     | `{ to, template, vars }`                              |
| POST   | `/v1/notifications/sms`       | `{ to, template, vars }`                              |
| POST   | `/v1/notifications/push`      | `{ deviceToken, template, vars }`                     |
| GET    | `/v1/notifications/:id`       | —                                                     |
| GET    | `/healthz`                    | —                                                     |

### Templates

Built in: `welcome`, `password_reset`, `txn_alert`, `statement_ready`.

## Env vars

See `.env.example`.

## Tests

None. `npm test` is a no-op.
