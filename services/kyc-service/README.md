# kyc-service

Mock identity verification + sanctions screening.

## Endpoints

| Method | Path                          | Description                                  |
|--------|-------------------------------|----------------------------------------------|
| POST   | `/v1/kyc/verify`              | Submit doc + selfie (base64). Returns id.    |
| GET    | `/v1/kyc/{verificationId}`    | Status: PENDING/APPROVED/REJECTED.           |
| POST   | `/v1/kyc/sanctions-check`     | Name + DOB screening.                        |
| POST   | `/v1/kyc/callback`            | Webhook from upstream provider (mocked).     |

## Run

```bash
pip install -e .
pip install -e ../../shared-libs/py-commons
uvicorn app.main:app --port 8090 --reload
```

## Environment variables

| Name                 | Default                  | Notes                              |
|----------------------|--------------------------|------------------------------------|
| `AUDIT_SERVICE_URL`  | `http://localhost:8089`  | Audit emit target.                 |
| `KYC_AUTO_DECIDE`    | `true`                   | If true, decisions land immediately. |

## Tests

```bash
pytest
```
