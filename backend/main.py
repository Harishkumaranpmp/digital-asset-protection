"""
SportShield — Main FastAPI Application
The central API gateway for the Digital Asset Protection Platform
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.config import get_settings
from backend.database import create_tables
from backend.routes.auth_routes import router as auth_router
from backend.routes.asset_routes import router as asset_router
from backend.routes.detection_routes import router as detection_router
from backend.routes.enforcement_routes import router as enforcement_router
from backend.routes.report_routes import alerts_router, reports_router
from backend.routes.health_routes import router as health_router

settings = get_settings()

# ── Structured Logging ────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sportshield")

# ── Sentry Error Tracking (production only) ───────────────────
try:
    import sentry_sdk
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.2,
            environment=os.getenv("APP_ENV", "development"),
        )
        logger.info("Sentry error tracking initialized.")
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    # Initialize database
    create_tables()
    
    # Ensure upload directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(f"{settings.UPLOAD_DIR}/thumbnails").mkdir(exist_ok=True)
    
    print(f"[SportShield] API v{settings.APP_VERSION} starting...")
    print(f"[SportShield] Upload directory: {os.path.abspath(settings.UPLOAD_DIR)}")
    print(f"[SportShield] Database: {settings.DATABASE_URL}")
    
    yield
    
    print("[SportShield] API shutting down...")


# ─── App Instance ─────────────────────────────────────────────

app = FastAPI(
    title="SportShield API",
    description="""
## 🛡️ SportShield — Digital Asset Protection for Sports Media

AI-powered platform that protects sports media from piracy, duplication, 
and unauthorized redistribution.

### Features
- **Digital Fingerprinting** — Perceptual hash signatures for every asset
- **Web Detection** — Automated scanning across web & social media
- **AI Analysis** — Google Gemini Vision for content intelligence
- **Legal Enforcement** — Automated DMCA & C&D notice generation
- **Real-time Alerts** — Instant notifications on new infringements
- **Reporting** — CSV/PDF export for executives and legal teams

### Authentication
Use Bearer token authentication. Get your token from `/api/auth/login`.

```
Authorization: Bearer <your_token>
```
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS — Production Hardened ──────────────────────────────
is_production = os.getenv("APP_ENV") == "production"

# In production, we combine the configured origins with common Render patterns
cors_origins = settings.ALLOWED_ORIGINS.copy()
if not is_production:
    cors_origins = ["*"]
else:
    # Always allow localhost for debugging even in prod-like envs if needed
    if "http://localhost:3000" not in cors_origins:
        cors_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    expose_headers=["Content-Disposition"],
)

# Block requests from unexpected hosts in production
if is_production:
    # Allow all onrender subdomains and common local hosts
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*.onrender.com", "*.run.app", "localhost", "127.0.0.1", "*"] 
    )


# ── API Routers ─────────────────────────────────────────────

app.include_router(health_router)        # GET /health/*
app.include_router(auth_router)          # POST /api/auth/*
app.include_router(asset_router)         # /api/assets/*
app.include_router(detection_router)     # /api/detections/*
app.include_router(enforcement_router)   # /api/enforcement/*
app.include_router(alerts_router)        # /api/alerts/*
app.include_router(reports_router)       # /api/reports/*


# ─── Health Check ────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "SportShield API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}


# ─── Serve Uploads (Static Files) ─────────────────────────────
uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")
