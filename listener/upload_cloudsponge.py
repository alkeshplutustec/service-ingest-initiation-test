import hashlib
import json
import logging
import math
import requests

from common_configs import env
from common_configs.aws_storage import AwsStorage, STORAGE_CLOUDSPONGE_FOLDER, STORAGE_USER_BUCKET
from common_configs.listener.resource import Resource
from common_configs.message_bus import MessageBus
from common_configs.queue import UPLOAD_CLOUDSPONGE_BATCH

from common_configs.service import RABBIT_MGT_HOST, RABBIT_MGT_PORT, RABBIT_VHOST, RABBIT_USER, RABBIT_PASS, \
    SVC_INGESTION_QUEUE
from conf.config import RABBIT_INGESTION_REPLICAS

from ingestion.ingestion_task import IngestionTask

logger = logging.getLogger("service_ingestion_logger")


class IngestCloudSponge(Resource):
    def __init__(self):
        batch_size = 5
        storage = AwsStorage(STORAGE_USER_BUCKET)

    def listen(self, ch, method, properties, body):
        data = json.loads(body.decode('utf-8'))

        if RABBIT_INGESTION_REPLICAS:
            routing_key = self._get_queue_replica_topic(RABBIT_INGESTION_REPLICAS,
                                                        UPLOAD_CLOUDSPONGE_BATCH,
                                                        SVC_INGESTION_QUEUE)
        else:
            routing_key = UPLOAD_CLOUDSPONGE_BATCH

        filename = data.get('filename')
        user_id = data.get('user_id')
        redis_key_root = filename.replace('/', '.')

        # ingestion = ProspectIngestion()
        file_content = self.storage.get_file(filename)
        # may need to rework
        content_data = json.loads(file_content.decode('utf-8'))

        service = content_data.get('service')
        content_data = content_data.get('contacts')
        prospect_count = len(content_data)

        logger.info("Ingesting file ({}) for {}".format(filename, user_id))

        batch = []
        counter = 0
        batch_counter = 0
        batch_total = int(math.ceil(float(prospect_count) / self.batch_size))

        for prospect in content_data:
            prospect["_service"] = service
            batch.append(prospect)
            counter += 1

            if counter % self.batch_size == 0 or counter == prospect_count:
                batch_counter += 1
                data = {
                    "redis_key_root": redis_key_root,
                    "user_id": user_id,
                    "prospects": batch,
                    "batch_counter": batch_counter,
                    "batch_total": batch_total
                }

                MessageBus().send(routing_key, json.dumps(data, sort_keys=True))
                logger.info("[RABBITCONN] - Batch message {} of {} for file {}".format(batch_counter, batch_total,
                                                                                       redis_key_root))
                batch = []

    @staticmethod
    def _get_queue_replica_topic(queue_replicas, base_routine_key, ingestion_queue):
        # get first replica stats
        rabbit_url = 'http://{}:{}/api/queues/{}/{}-{}'.format(RABBIT_MGT_HOST, str(RABBIT_MGT_PORT), RABBIT_VHOST,
                                                               ingestion_queue, '0')
        req = requests.get(url=rabbit_url, auth=(RABBIT_USER, RABBIT_PASS))
        message_len = json.loads(req.text).get('messages')

        if message_len == 0:
            return '{}-0'.format(base_routine_key)

        min_replica = {"replica": 0, "count": message_len}

        for replica in range(1, int(queue_replicas)):
            rabbit_url = 'http://{}:{}/api/queues/{}/{}-{}'.format(RABBIT_MGT_HOST, str(RABBIT_MGT_PORT), RABBIT_VHOST, ingestion_queue, replica)
            req = requests.get(url=rabbit_url, auth=(RABBIT_USER, RABBIT_PASS))
            message_len = json.loads(req.text).get('messages')

            if message_len == 0:
                return '{}-{}'.format(base_routine_key, str(replica))

            if message_len < min_replica.get('count'):
                min_replica['replica'] = replica
                min_replica['count'] = message_len

        return '{}-{}'.format(base_routine_key, str(min_replica.get('replica')))
