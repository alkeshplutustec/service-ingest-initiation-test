#!/bin/bash

set -e
REGISTRY="us.gcr.io/advisorconnect-1238/"
IMAGE="service-ingest-initiation"
#set image tag
if [ $CI_BRANCH != "production" ]; then
    IMAGE_TAG=${CI_BRANCH}-${CI_TIMESTAMP}-${CI_COMMIT_ID}-${CI_COMMITTER_USERNAME}
else
    IMAGE_TAG=2.1.0-${CI_TIMESTAMP}-${CI_COMMIT_ID}-${CI_COMMITTER_USERNAME}
fi

# authenticate google cloud
codeship_google authenticate

# set compute zone
gcloud config set compute/zone us-east1-b

# set kubernetes cluster
gcloud container clusters get-credentials london

echo deploying image: ${IMAGE}:${IMAGE_TAG}
# update kubernetes Deployment
GOOGLE_APPLICATION_CREDENTIALS=/keyconfig.json \
    kubectl set image deployment/svc-ingest-initiation-${CI_BRANCH} \
    --namespace=${CI_BRANCH} \
    svc-ingest-initiation-$CI_BRANCH=${REGISTRY}${IMAGE}:${IMAGE_TAG}