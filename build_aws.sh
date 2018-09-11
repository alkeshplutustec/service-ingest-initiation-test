#!/usr/bin/env bash
#
#  Build and push ingest-initiation service
#

AWS_ACCT="603278562063"
AWS_REGION="us-east-1"
IMAGE="ac-service-ingest-initiation"

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -a|--account)
    AWS_ACCT="${2:-AWS_ACCT}"
    shift # past argument
    shift # past value
    ;;
    -r|--region)
    AWS_REGION="${2:-AWS_REGION}"
    shift # past argument
    shift # past value
    ;;
    -v|--version)
    VERSION="$2"
    shift # past argument
    shift # past value
    ;;
esac
done

if [ -z ${VERSION+x} ]; 
	then echo "Please specify version with a -v or --version flag.";
	return 0
fi

REGISTRY="${AWS_ACCT}.dkr.ecr.${AWS_REGION}.amazonaws.com/"

eval $(aws ecr get-login --no-include-email --region ${AWS_REGION}  | sed 's|https://||')

echo "Building locally using docker builder..."
docker build -t ${IMAGE}:${VERSION} .

echo "Tagging image as version ${VERSION}"
docker tag ${IMAGE}:${VERSION} ${AWS_ACCT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE}:${VERSION}

echo "Pushing image to ECR registry"
docker push ${AWS_ACCT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE}:${VERSION}
