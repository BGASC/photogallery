#!/bin/bash
source ./set_env_vars_for_photo_gallery.sh

echo "Creating service account..."
gcloud iam service-accounts create $SA_NAME \
  --display-name="GitHub Actions Deployment SA" \
  --project=$PROJECT_ID || true

SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo "Granting roles..."
for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/artifactregistry.writer roles/artifactregistry.admin; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE"
done
echo "Service Account configured: $SA_EMAIL"
