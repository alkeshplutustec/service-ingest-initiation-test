#!/usr/bin/env bash

# TODO: write logs to google storage
uwsgi --ini $PWD/conf/uwsgi.conf --daemonize2 true $@
export NEW_RELIC_CONFIG_FILE=newrelic/newrelic-${ENVIRONMENT}.ini
newrelic-admin run-program python listener.py