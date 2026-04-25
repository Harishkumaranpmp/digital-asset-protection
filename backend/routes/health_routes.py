"""
SportShield — Production Health & Diagnostics Routes
Provides detailed system status for monitoring tools (Cloud Run, Kubernetes, Sentry)
"""

import os
import time
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import get_db
from backend.config import get_settings

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])
settings = get_settings()

# Track app start time for uptime reporting
_START_TIME = time.time()


@router.get("/")
def health_check():
    """
    Basic health check. Used by Cloud Run / load balancers.
    Returns 200 OK as long as the process is alive.
    """
    return {
        "status": "healthy",
        "service": "SportShield API",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check. Verifies all critical dependencies (DB, storage) are reachable.
    Cloud Run uses this to decide when to start sending traffic.
    """
    checks = {}
    all_healthy = True

    # ── Database check ───────────────────────────────────────
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "type": settings.DATABASE_URL.split(":")[0]}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
        all_healthy = False

    # ── Redis/Celery check ───────────────────────────────────
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = {"status": "ok"}
    except Exception as e:
        # Redis is optional — degrade gracefully
        checks["redis"] = {"status": "degraded", "detail": "Celery tasks unavailable"}

    # ── Storage check ────────────────────────────────────────
    upload_dir = settings.UPLOAD_DIR
    checks["storage"] = {
        "status": "ok" if os.path.isdir(upload_dir) else "error",
        "path": upload_dir,
        "writable": os.access(upload_dir, os.W_OK) if os.path.isdir(upload_dir) else False,
    }
    if checks["storage"]["status"] == "error":
        all_healthy = False

    # ── AI Models check ──────────────────────────────────────
    try:
        from ai_models.fingerprint_generator import FingerprintGenerator
        checks["ai_engine"] = {"status": "ok", "module": "FingerprintGenerator"}
    except ImportError as e:
        checks["ai_engine"] = {"status": "error", "detail": str(e)}
        all_healthy = False

    status_code = 200 if all_healthy else 503
    return {
        "status": "ready" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


@router.get("/live")
def liveness_check():
    """
    Liveness check. If this returns an error, the container is restarted.
    Only fails if the process is in a truly broken state.
    """
    return {"status": "alive", "pid": os.getpid()}


@router.get("/metrics")
def metrics_summary(db: Session = Depends(get_db)):
    """
    High-level performance metrics for dashboards and monitoring.
    (Non-sensitive — no auth required for internal use)
    """
    from backend.database import Asset, Detection, EnforcementCase, User
    try:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(time.time() - _START_TIME, 2),
            "counts": {
                "users": db.query(User).count(),
                "assets": db.query(Asset).count(),
                "detections": db.query(Detection).count(),
                "enforcement_cases": db.query(EnforcementCase).count(),
            }
        }
    except Exception:
        return {"timestamp": datetime.utcnow().isoformat(), "counts": "unavailable"}
