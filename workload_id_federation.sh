#!/bin/bash
source ./set_env_vars_for_photo_gallery.sh

echo "Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Pool" \
  --project=$PROJECT_ID || true

echo "Creating OIDC Provider..."
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '$GITHUB_REPO'" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --project=$PROJECT_ID || true

echo "Binding GitHub repo to Service Account..."
gcloud iam service-accounts add-iam-policy-binding "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/$GITHUB_REPO" \
  --project=$PROJECT_ID

echo "--------------------------------------------------------"
echo "Save this WORKLOAD_IDENTITY_PROVIDER string for your YAML:"
echo "projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
echo "--------------------------------------------------------"
