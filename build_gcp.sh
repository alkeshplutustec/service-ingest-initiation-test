#!/usr/bin/env bash
#
#  Build and push search service
#

REGISTRY="us.gcr.io/advisorconnect-1238/"
IMAGE="service-ingest-initiation"
VERSION="develop"
#VERSION="staging"
#VERSION="2.1.0"

gcloud components install alpha

echo "Building remotely using gcloud container builder..."
echo "If this fails, please ensure you have gcloud alpha components installed,"
echo "or try building locally with docker."

####################################
# Build using Google Cloud Builder #
####################################
gcloud alpha container builds create . --tag ${REGISTRY}${IMAGE}:${VERSION}

#################
# Build locally #
#################
#gcloud docker -a
#docker build --rm -t ${REGISTRY}${IMAGE}:${VERSION} .
#docker push ${REGISTRY}${IMAGE}:${VERSION}
#docker tag  ${REGISTRY}${IMAGE}:${VERSION} ${REGISTRY}${IMAGE}:latest
#docker push ${REGISTRY}${IMAGE}:latest

