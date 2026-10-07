#!/usr/bin/env bash
set -euo pipefail

# Project 1.27 New Ground Match Agent - Infrastructure Setup
PROJECT_ID="new-ground-mentor-matching"
REGION="us-central1"

echo "=== Step 1: Setting GCP Project: ${PROJECT_ID} ==="
gcloud config set project "${PROJECT_ID}"

echo "=== Step 2: Enabling Required GCP Services ==="
SERVICES=(
  "run.googleapis.com"
  "bigquery.googleapis.com"
  "aiplatform.googleapis.com"
  "secretmanager.googleapis.com"
  "cloudscheduler.googleapis.com"
  "iap.googleapis.com"
  "cloudbuild.googleapis.com"
  "artifactregistry.googleapis.com"
  "iam.googleapis.com"
  "gmail.googleapis.com"
  "cloudresourcemanager.googleapis.com"
)

for svc in "${SERVICES[@]}"; do
  echo "Enabling ${svc}..."
  gcloud services enable "${svc}" --project="${PROJECT_ID}"
done

echo "=== Step 3: Creating BigQuery Datasets (US) ==="
bq show --dataset "${PROJECT_ID}:new_ground" >/dev/null 2>&1 || \
  bq mk --dataset --location=US --description="New Ground Production Dataset (Synthetic)" --label datacloud:antigravity "${PROJECT_ID}:new_ground"

bq show --dataset "${PROJECT_ID}:new_ground_dev" >/dev/null 2>&1 || \
  bq mk --dataset --location=US --description="New Ground Dev Dataset (Synthetic)" --label datacloud:antigravity "${PROJECT_ID}:new_ground_dev"

echo "=== Step 4: Creating Artifact Registry Repository ==="
gcloud artifacts repositories describe new-ground-repo --location="${REGION}" >/dev/null 2>&1 || \
  gcloud artifacts repositories create new-ground-repo \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker repo for New Ground apps"

echo "=== Step 5: Creating Service Accounts ==="
# sa-coordinator-app
gcloud iam service-accounts describe "sa-coordinator-app@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1 || \
  gcloud iam service-accounts create sa-coordinator-app \
    --display-name="Coordinator App Service Account"

# sa-response-portal
gcloud iam service-accounts describe "sa-response-portal@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1 || \
  gcloud iam service-accounts create sa-response-portal \
    --display-name="Response Portal Service Account"

echo "=== Step 6: Granting IAM Roles to Coordinator Service Account ==="
COORDINATOR_SA="sa-coordinator-app@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${COORDINATOR_SA}" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${COORDINATOR_SA}" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${COORDINATOR_SA}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${COORDINATOR_SA}" \
  --role="roles/secretmanager.secretAccessor"

echo "=== Step 7: Granting IAM Roles to Portal Service Account (Least-Privilege) ==="
PORTAL_SA="sa-response-portal@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PORTAL_SA}" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PORTAL_SA}" \
  --role="roles/secretmanager.secretAccessor"

echo "=== Step 8: Initializing Secret Manager Secrets ==="
if ! gcloud secrets describe link-signing-key >/dev/null 2>&1; then
  openssl rand -hex 32 | gcloud secrets create link-signing-key --data-file=-
fi

if ! gcloud secrets describe gmail-sender-oauth >/dev/null 2>&1; then
  echo -n "{}" | gcloud secrets create gmail-sender-oauth --data-file=-
fi

echo "=== Step 9: Granting IAP Access to Coordinators ==="
COORDINATORS=("mgomez@project127.org" "adudrey@project127.org" "akuykendall@project127.org")
for user in "${COORDINATORS[@]}"; do
  echo "Granting IAP role to ${user}..."
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="user:${user}" \
    --role="roles/iap.httpsResourceAccessor" || echo "Note: If domain is external, grant directly in IAP console."
done

echo "=== Setup complete! Please review infra/MANUAL_STEPS.md ==="
