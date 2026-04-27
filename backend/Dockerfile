# ============================================================
# SportShield — Production Dockerfile
# Multi-stage build for minimal, secure production image
# ============================================================

# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for OpenCV, Pillow, and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production Runtime ───────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

# Install only runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 sportshield && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false sportshield

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=sportshield:sportshield . .

# Create required runtime directories with correct permissions
RUN mkdir -p /app/uploads/thumbnails /app/uploads/temp /app/logs && \
    chown -R sportshield:sportshield /app/uploads /app/logs

# Switch to non-root user
USER sportshield

# Expose API port
EXPOSE 8000

# Health check (Cloud Run compatibility)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production server: Gunicorn + Uvicorn workers
# Workers = (2 * CPU_CORES) + 1 — set via environment variable
CMD sh -c 'gunicorn backend.main:app \
     --worker-class uvicorn.workers.UvicornWorker \
     --workers ${GUNICORN_WORKERS:-2} \
     --bind 0.0.0.0:8000 \
     --timeout 120 \
     --keep-alive 5 \
     --max-requests 1000 \
     --max-requests-jitter 100 \
     --access-logfile - \
     --error-logfile - \
     --log-level info'
