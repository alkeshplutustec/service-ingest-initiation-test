# coding=utf-8
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("service_ingestion_logger")


# refactor into ABC
class IngestionTask(object):

    # TODO: Remove?
    log = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()

    @abstractmethod
    def process(self, *args, **kwargs):
        pass