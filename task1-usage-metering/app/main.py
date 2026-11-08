import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.database.session import engine
from app.database.base import Base
import app.models  # Ensure all models are registered with Base metadata

from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.usage import router as usage_router
from app.api.v1.caps import router as caps_router
from app.api.v1.health import router as health_router
from app.api.v1.reconciliation import router as reconciliation_router
from app.api.v1.accounts import router as accounts_router

# Initialize tables automatically for SQLite/Dev
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Metadata create_all notice: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="High-throughput, idempotent backend usage metering service for telephony call events.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_and_logging_middleware(request: Request, call_next):
    # Correlation ID propagation
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    response.headers["X-Correlation-ID"] = correlation_id

    # Structured request logging
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
        extra={
            "correlation_id": correlation_id,
            "extra_data": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown"
            }
        }
    )

    return response


# Include Routers
# Mount webhooks at both root and /api/v1 for maximum compatibility
app.include_router(webhooks_router)
app.include_router(webhooks_router, prefix="/api/v1")

app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")

app.include_router(usage_router, prefix="/api/v1")
app.include_router(caps_router, prefix="/api/v1")
app.include_router(reconciliation_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "health": "/health",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
