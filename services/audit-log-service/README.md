# audit-log-service

Append-only collector for `AuditEvent` records emitted by other services.

## Endpoints

| Method | Path                  | Description                          |
|--------|-----------------------|--------------------------------------|
| POST   | `/v1/events`          | Append an event.                     |
| GET    | `/v1/events`          | List/filter events.                  |
| GET    | `/v1/events/{id}`     | Fetch a single event.                |
| GET    | `/v1/events/_health`  | Liveness.                            |

### `GET /v1/events` filters

`service`, `actor`, `action`, `resource_type`, `resource_id`, `since`, `until`,
`limit` (default 100), `offset` (default 0).

## Run

```bash
pip install -e .
pip install -e ../../shared-libs/py-commons
uvicorn app.main:app --port 8089 --reload
```

## Environment variables

| Name                 | Default | Notes                                |
|----------------------|---------|--------------------------------------|
| `AUDIT_MAX_EVENTS`   | `50000` | Soft cap before oldest are dropped.  |

## Tests

None. `pytest` collects zero items. Listed on the backlog.
