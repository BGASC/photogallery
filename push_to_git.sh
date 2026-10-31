#!/bin/bash
source ./set_env_vars_for_photo_gallery.sh
git init
git branch -M main
git remote set-url origin https://github.com/$GITHUB_REPO.git 2>/dev/null || git remote add origin https://github.com/$GITHUB_REPO.git
git add .
git commit -m "Configure GCP automation scripts and files" || true
git push -u origin main
