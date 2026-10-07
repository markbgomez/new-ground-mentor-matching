#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="new-ground-mentor-matching"
REGION="us-central1"

echo "=== Tearing Down Cloud Run Services ==="
gcloud run services delete coordinator-app --region="${REGION}" --quiet || true
gcloud run services delete response-portal --region="${REGION}" --quiet || true

echo "=== Teardown Completed ==="
