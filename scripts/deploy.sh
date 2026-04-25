#!/usr/bin/env bash
# ============================================================
# SportShield — One-Command Production Deployment Script
# Usage: chmod +x scripts/deploy.sh && ./scripts/deploy.sh
# ============================================================

set -e  # Exit immediately on error
set -u  # Error on undefined variables

# ── Colors ────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✅  OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[⚠️  WARN]${NC} $1"; }
error()   { echo -e "${RED}[❌ ERROR]${NC} $1"; exit 1; }

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🛡️  SportShield Production Deployer   ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── Step 1: Pre-flight Checks ─────────────────────────────────
info "Running pre-flight checks..."
command -v docker >/dev/null 2>&1 || error "Docker is not installed."
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is not installed."
[ -f ".env.production" ] || error ".env.production not found. Copy .env.production.template and fill in values."
success "Pre-flight checks passed."

# ── Step 2: Load Environment ──────────────────────────────────
info "Loading production environment..."
set -a; source .env.production; set +a
success "Environment loaded."

# ── Step 3: Pull Latest Code ──────────────────────────────────
info "Pulling latest code from git..."
git pull origin main
success "Code is up to date."

# ── Step 4: Build Docker Images ───────────────────────────────
info "Building production Docker images (this may take a few minutes)..."
docker compose -f docker-compose.prod.yml build --no-cache
success "Docker images built."

# ── Step 5: Stop Existing Services ────────────────────────────
info "Stopping existing services (zero-downtime swap)..."
docker compose -f docker-compose.prod.yml down --remove-orphans || true
success "Old services stopped."

# ── Step 6: Start All Services ────────────────────────────────
info "Starting all production services..."
docker compose -f docker-compose.prod.yml up -d
success "Services started."

# ── Step 7: Wait for DB ───────────────────────────────────────
info "Waiting for PostgreSQL to be ready..."
RETRIES=15
until docker compose -f docker-compose.prod.yml exec -T db pg_isready -U "${POSTGRES_USER:-sportshield}" >/dev/null 2>&1 || [ $RETRIES -le 0 ]; do
    RETRIES=$((RETRIES - 1))
    echo -n "."
    sleep 2
done
echo ""
[ $RETRIES -gt 0 ] && success "Database is ready." || error "Database failed to start."

# ── Step 8: Seed Database ─────────────────────────────────────
info "Seeding database (admin user + org)..."
docker compose -f docker-compose.prod.yml exec -T api python scripts/seed_db.py
success "Database seeded."

# ── Step 9: Health Check ──────────────────────────────────────
info "Running health check..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
[ "$HTTP_STATUS" = "200" ] && success "API is healthy (HTTP $HTTP_STATUS)." || error "Health check failed (HTTP $HTTP_STATUS)."

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🚀 SportShield is LIVE!               ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  API:        ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:   ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  Health:     ${BLUE}http://localhost:8000/health/ready${NC}"
echo ""
echo -e "  Admin Login:"
echo -e "  Email:    ${YELLOW}admin@sportshield.ai${NC}"
echo -e "  Password: ${YELLOW}SportShield2024!${NC} (change immediately)"
echo ""
