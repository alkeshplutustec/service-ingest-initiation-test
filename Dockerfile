#FROM us.gcr.io/advisorconnect-1238/python3:latest
FROM 603278562063.dkr.ecr.us-east-1.amazonaws.com/ac-python3:latest
MAINTAINER <chris@advisorconnect.co>

#LABEL co.advisorconnect.image=gcr.io/advisorconnect-1238/service-ingest-initiation
LABEL co.advisorconnect.image=603278562063.dkr.ecr.us-east-1.amazonaws.com/ac-service-ingest-initiation

#
# ONBUILD commands that run as a reuslt of instructions from
#         the parent container:
#
#    * requirements.txt is copied to the container
#    * pip install of the requirements is run
#    * All source co-located with the Dockerfile is copied
#      to /usr/local/app
#

CMD ["bash", "./run.sh"]
