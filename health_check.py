# coding=utf-8
"""
Kubernetes Health-check and Liveness Probe
See "ExecAction"
http://kubernetes.io/docs/user-guide/pod-states/#container-probes
ExecAction: executes a specified command inside the container expecting on success that the command exits with status code 0.
/usr/src/app
"""
# from flask import request, make_response
# from flask_restful import Resource

import sys
import click
import psutil
import requests

@click.group()
def cli():
    pass

@cli.command("liveness")
def check_liveness():
    """Check the responsiveness of a pod"""

    # # look for running server process
    # server_live = healthy_server()

    # look for running listener process
    listener_live = healthy_listener()

    # # look for at least 2 running celery processe
    # celery_worker_threshold = 2
    # celery_live = healthy_celery(celery_worker_threshold)

    if listener_live:
        return healthy()
    else:
        return unhealthy()

@cli.command("readiness")
def check_ready():
    """Check the pod's readiness to service requests"""

    # # look for running server process
    # server_live = healthy_server()

    # look for running listener process
    listener_live = healthy_listener()

    # # look for at least 2 running celery processe
    # celery_worker_threshold = 2
    # celery_live = healthy_celery(celery_worker_threshold)

    if listener_live:
        return ready()
    else:
        return not_ready()

def healthy_server():
    r = requests.get(url='http://localhost/healthz')
    r.connection.close()
    if r.status_code is 200:
        return True
    return False

def healthy_listener():
    for pid in psutil.pids():
        p = psutil.Process(pid)
        try:
            if p.name().lower() == "python" and "listener.py" in p.cmdline():
                return True
        # pass on zombie processes
        except Exception:
            pass
    return False

def healthy_celery(celery_worker_threshold):
    celery_worker_count = 0

    for pid in psutil.pids():
        p = psutil.Process(pid)
        try:
            if "python" in p.name().lower() and "celery" in p.cmdline():
                celery_worker_count += 1
        # pass on zombie processes
        except Exception:
            pass

    if celery_worker_count > celery_worker_threshold:
        return True

    return False

def healthy():
    """
    Indicates a healthy pod.
    return: Exit status of 0 (Kubernetes 'healthy'.)
    """
    sys.exit(0)


def unhealthy():
    """
    Indicates the pod is unhealthy or unresponsive
    :return: Exit status of 1 (Kubernetes 'unhealthy')
    """
    sys.exit(1)


def ready():
    """
    Indicates pod is ready to service requests.
    return: Exit status of 0 (Kubernetes 'healthy'.)
    """
    sys.exit(0)


def not_ready():
    """
    Indicates pod is not ready to service requests.
    return: Exit status of 1 (Kubernetes 'not-ready'.)
    """
    sys.exit(1)


if __name__ == '__main__':
    cli()
