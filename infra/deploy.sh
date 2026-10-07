#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="new-ground-mentor-matching"
REGION="us-central1"
REPO="new-ground-repo"

echo "=== Deploying New Ground Match Agent ==="
echo "Target Project: ${PROJECT_ID}"
echo "Target Region: ${REGION}"

# Safety check for demo mode
PRODUCTION=false
for arg in "$@"; do
  if [ "$arg" == "--production" ]; then
    PRODUCTION=true
  fi
done

if [ "$PRODUCTION" != "true" ]; then
  echo ">>> RUNNING IN DEMO MODE (All email redirected to mgomez@project127.org) <<<"
else
  echo ">>> WARNING: PRODUCTION MODE REQUESTED <<<"
fi

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

echo "=== Building Coordinator Container Image ==="
gcloud builds submit --tag "${IMAGE_BASE}/coordinator-app:latest" .

echo "=== Building Response Portal Container Image ==="
gcloud builds submit --config=cloudbuild-portal.yaml --substitutions="_IMAGE=${IMAGE_BASE}/response-portal:latest" .

echo "=== Deploying Coordinator App to Cloud Run ==="
gcloud run deploy coordinator-app \
  --image="${IMAGE_BASE}/coordinator-app:latest" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="sa-coordinator-app@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID},GCP_REGION=${REGION},BIGQUERY_DATASET=new_ground,DEMO_MODE=true" \
  --allow-unauthenticated

echo "=== Deploying Response Portal to Cloud Run (Public) ==="
gcloud run deploy response-portal \
  --image="${IMAGE_BASE}/response-portal:latest" \
  --region="${REGION}" \
  --platform=managed \
  --service-account="sa-response-portal@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID},GCP_REGION=${REGION},BIGQUERY_DATASET=new_ground,DEMO_MODE=true" \
  --allow-unauthenticated

echo "=== Deployment Completed Successfully! ==="
COORDINATOR_URL=$(gcloud run services describe coordinator-app --region="${REGION}" --format='value(status.url)')
PORTAL_URL=$(gcloud run services describe response-portal --region="${REGION}" --format='value(status.url)')

echo "Coordinator App URL: ${COORDINATOR_URL}"
echo "Response Portal URL: ${PORTAL_URL}"
