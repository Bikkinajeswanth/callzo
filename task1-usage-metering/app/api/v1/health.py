import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.models.webhook_event import RawWebhookEvent
from app.models.call import Call
from app.core.config import settings

router = APIRouter(tags=["Health & Monitoring"])

START_TIME = time.time()


@router.get("/health", summary="Health and Readiness Check")
def health_check(response: Response, db: Session = Depends(get_db)):
    db_ok = False
    db_latency_ms = 0.0

    t0 = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        db_ok = True
    except Exception as e:
        db_ok = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    uptime_seconds = round(time.time() - START_TIME, 1)

    # Core operational metrics
    total_events = 0
    total_calls = 0
    if db_ok:
        try:
            total_events = db.query(RawWebhookEvent).count()
            total_calls = db.query(Call).count()
        except Exception:
            pass

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "database": {
            "connected": db_ok,
            "latency_ms": db_latency_ms
        },
        "metrics": {
            "total_webhook_events_received": total_events,
            "total_calls_tracked": total_calls
        }
    }
