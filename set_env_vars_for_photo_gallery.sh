#!/bin/bash
export PROJECT_ID=$(gcloud config get-value project)
export GITHUB_REPO="bgasc/photogallery"
export SA_NAME="github-actions-sa"
export REGION="europe-west1"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Environment set for Project: $PROJECT_ID ($PROJECT_NUMBER), Repo: $GITHUB_REPO"
