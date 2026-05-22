# fraud-detection-service

Rule-engine and ML-style scoring for retail-banking transactions.

## Endpoints

| Method | Path                | Description                              |
|--------|---------------------|------------------------------------------|
| POST   | `/v1/score`         | Score a transaction (0-100 risk).        |
| GET    | `/v1/rules`         | List active rules.                       |
| POST   | `/v1/rules`         | Add a rule (admin).                      |
| GET    | `/v1/scores/{txn}`  | Fetch a previously computed score.       |

## Run

```bash
pip install -e .
# Or include the shared lib as an editable install:
pip install -e ../../shared-libs/py-commons
uvicorn app.main:app --port 8088 --reload
```

## Environment variables

| Name                   | Default                  | Notes                                  |
|------------------------|--------------------------|----------------------------------------|
| `AUDIT_SERVICE_URL`    | `http://localhost:8089`  | URL of audit-log-service.              |
| `VELOCITY_WINDOW_MIN`  | `5`                      | Window for per-customer txn velocity.  |
| `VELOCITY_THRESHOLD`   | `5`                      | Txn count threshold inside window.     |
| `HIGH_AMOUNT_USD`      | `10000`                  | High-amount rule cutoff (USD).         |

## Tests

```bash
pytest
```
