import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings, setup_logging
from app.database import init_db
from app.routes import router as items_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting application", extra={"app": settings.app_name})
    await init_db()
    yield
    logger.info("Shutting down application")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    if request.url.path not in ("/health", "/metrics"):
        logger.info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client": request.client.host if request.client else None,
            },
        )
    return response


app.include_router(items_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
