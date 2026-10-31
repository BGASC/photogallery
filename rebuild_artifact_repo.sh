#!/bin/bash
source ./set_env_vars_for_photo_gallery.sh
gcloud artifacts repositories create app-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="Repository for Photo Gallery App" \
  --project=$PROJECT_ID || true
echo "Artifact Registry repository ready."
