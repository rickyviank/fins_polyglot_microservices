from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from finspoly_commons import DomainError, NotFoundError, UnauthorizedError, ValidationError

from .routers import scoring

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="fraud-detection-service", version="0.3.1")
app.include_router(scoring.router)


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

    uvicorn.run("app.main:app", host="0.0.0.0", port=8088, reload=False)
