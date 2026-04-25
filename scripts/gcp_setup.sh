#!/usr/bin/env bash
# ============================================================
# SportShield — Google Cloud Platform Setup Script
# Run this ONCE to provision your GCP infrastructure
# Usage: chmod +x scripts/gcp_setup.sh && ./scripts/gcp_setup.sh
# ============================================================

set -e

# ── Configuration — EDIT THESE ───────────────────────────────
PROJECT_ID="your-gcp-project-id"      # Your GCP Project ID
REGION="us-central1"
BUCKET_NAME="sportshield-media-$(echo $PROJECT_ID | tr -d '-')"
SERVICE_ACCOUNT="sportshield-sa"
DB_INSTANCE="sportshield-pg"
DB_NAME="sportshield"
DB_USER="sportshield"
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
info() { echo -e "${BLUE}[GCP]${NC} $1"; }
success() { echo -e "${GREEN}[✅]${NC} $1"; }

# ── Step 1: Set Project ───────────────────────────────────────
info "Setting active GCP project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# ── Step 2: Enable APIs ───────────────────────────────────────
info "Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    logging.googleapis.com
success "APIs enabled."

# ── Step 3: Create Service Account ───────────────────────────
info "Creating service account: $SERVICE_ACCOUNT"
gcloud iam service-accounts create $SERVICE_ACCOUNT \
    --display-name="SportShield Service Account" \
    --description="Used by Cloud Run and local Docker" 2>/dev/null || true

SA_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"

# Grant necessary roles
for ROLE in \
    "roles/cloudsql.client" \
    "roles/storage.objectAdmin" \
    "roles/secretmanager.secretAccessor" \
    "roles/logging.logWriter"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" --quiet
done
success "Service account configured."

# ── Step 4: Create GCS Bucket ─────────────────────────────────
info "Creating Cloud Storage bucket: $BUCKET_NAME"
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME/ 2>/dev/null || true
gsutil cors set scripts/bucket-cors.json gs://$BUCKET_NAME/
gsutil uniformbucketlevelaccess set on gs://$BUCKET_NAME/
success "Bucket ready: gs://$BUCKET_NAME"

# ── Step 5: Create Cloud SQL (PostgreSQL) ─────────────────────
info "Provisioning Cloud SQL PostgreSQL instance (takes ~5 min)..."
gcloud sql instances create $DB_INSTANCE \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup \
    --enable-bin-log \
    2>/dev/null || info "Instance already exists, skipping."

gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE 2>/dev/null || true
gcloud sql users create $DB_USER --instance=$DB_INSTANCE --password="$DB_PASSWORD" 2>/dev/null || true
success "Cloud SQL ready."

# ── Step 6: Store Secrets in Secret Manager ───────────────────
info "Storing secrets in Google Secret Manager..."
DB_URL="postgresql+psycopg2://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE"

store_secret() {
    local NAME=$1; local VALUE=$2
    echo -n "$VALUE" | gcloud secrets create $NAME --data-file=- 2>/dev/null || \
    echo -n "$VALUE" | gcloud secrets versions add $NAME --data-file=-
}

store_secret "sportshield-db-url" "$DB_URL"
store_secret "sportshield-secret-key" "$(python3 -c "import secrets; print(secrets.token_hex(64))")"
store_secret "sportshield-jwt-secret" "$(python3 -c "import secrets; print(secrets.token_hex(64))")"
store_secret "sportshield-redis-url" "PLACEHOLDER_SET_UPSTASH_URL"
store_secret "sportshield-gemini-key" "PLACEHOLDER_SET_GEMINI_KEY"
success "Secrets stored."

# ── Step 7: Download Service Account Key ─────────────────────
info "Downloading service account key..."
mkdir -p secrets
gcloud iam service-accounts keys create secrets/gcp-service-account.json \
    --iam-account=$SA_EMAIL
success "Key saved to secrets/gcp-service-account.json"
echo "⚠️  Add secrets/ to .gitignore immediately!"

# ── Summary ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🎉 GCP Infrastructure Ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Project:    $PROJECT_ID"
echo "  Region:     $REGION"
echo "  Bucket:     gs://$BUCKET_NAME"
echo "  DB:         $DB_INSTANCE / $DB_NAME"
echo "  DB Password: $DB_PASSWORD (stored in Secret Manager)"
echo ""
echo "  Next: Push to main branch to trigger GitHub Actions deployment."
echo ""
