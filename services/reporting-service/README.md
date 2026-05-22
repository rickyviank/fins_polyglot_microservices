# reporting-service

Regulatory + operational reporting endpoints. Aggregates from txn-service and
fraud-detection-service (currently stubbed with fixture data).

## Endpoints

| Method | Path                            | Description                                  |
|--------|---------------------------------|----------------------------------------------|
| GET    | `/v1/reports/daily-summary`     | Daily transaction counts + volume.           |
| GET    | `/v1/reports/ctr`               | Currency Transaction Report (txns > $10k).   |
| GET    | `/v1/reports/sar-candidates`    | Suspicious Activity candidates.              |
| GET    | `/v1/reports/export`            | Export by id and format (`csv` or `json`).   |

## Run

```bash
pip install -e .
pip install -e ../../shared-libs/py-commons
uvicorn app.main:app --port 8091 --reload
```

## Environment variables

| Name                  | Default                  | Notes                              |
|-----------------------|--------------------------|------------------------------------|
| `AUDIT_SERVICE_URL`   | `http://localhost:8089`  | Audit emit target.                 |
| `TXN_SERVICE_URL`     | `http://localhost:8081`  | Transaction service (stubbed).     |
| `FRAUD_SERVICE_URL`   | `http://localhost:8088`  | Fraud service (stubbed).           |
| `REPORTS_DIR`         | `/tmp/reports`           | Working dir for bundled exports.   |

## Tests

No unit tests yet — see `services/reporting-service/TODO`.
