from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from finspoly_commons import DomainError, NotFoundError, UnauthorizedError, ValidationError

from .routers import kyc

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="kyc-service", version="0.1.4")
app.include_router(kyc.router)


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok"}


@app.exception_handler(NotFoundError)
async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"code": exc.code, "message": str(exc)})


@app.exception_handler(ValidationError)
async def _validation(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"code": exc.code, "message": str(exc)})


@app.exception_handler(UnauthorizedError)
async def _unauth(_: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"code": exc.code, "message": str(exc)})


@app.exception_handler(DomainError)
async def _domain(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"code": exc.code, "message": str(exc)})


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8090, reload=False)
