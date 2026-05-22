# finspoly-py-commons

Shared utilities for fins-polyglot Python services.

## Contents

- `finspoly_commons.Money`, `usd` — minor-unit money type.
- `finspoly_commons.validation` — email/account/SSN/Luhn validators.
- `finspoly_commons.AuditClient`, `AuditEvent` — best-effort audit emitter.
- `finspoly_commons.errors` — `DomainError`, `ValidationError`, `NotFoundError`, `UnauthorizedError`.

## Install / test

```
pip install -e ".[dev]"
pytest
```

Services depend on it via editable install path (`pip install -e ../../shared-libs/py-commons`).
