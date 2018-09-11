import hashlib
import json
import logging
import math
import requests

from common_configs import env
from common_configs.listener.resource import Resource
from common_configs.message_bus import MessageBus
from common_configs.aws_storage import AwsStorage, STORAGE_USER_BUCKET, STORAGE_GMAIL_AUTH0_SYNC_FOLDER
from common_configs.queue import UPLOAD_GMAIL_AUTH0_SYNC_BATCH

from common_configs.service import RABBIT_MGT_HOST, RABBIT_MGT_PORT, RABBIT_VHOST, RABBIT_USER, RABBIT_PASS, \
    SVC_INGESTION_QUEUE
from conf.config import RABBIT_INGESTION_REPLICAS

from ingestion.ingestion_task import IngestionTask

logger = logging.getLogger("service_ingestion_logger")


class IngestGmailAuth0Sync(Resource):
    def __init__(self):
        self.batch_size = 5
        self.storage = AwsStorage()

    def listen(self, ch, method, properties, body):
        data = json.loads(body.decode('utf-8'))

        if RABBIT_INGESTION_REPLICAS:
            routing_key = self._get_queue_replica_topic(RABBIT_INGESTION_REPLICAS,
                                                        UPLOAD_GMAIL_AUTH0_SYNC_BATCH,
                                                        SVC_INGESTION_QUEUE)
        else:
            routing_key = UPLOAD_GMAIL_AUTH0_SYNC_BATCH

        filename = data.get('filename')
        user_id = data.get('user_id')
        redis_key_root = filename.replace("/", ".")

        file_content = self.storage.get_file(filename)
        content_data = json.loads(file_content)
        prospect_count = len(content_data)

        if prospect_count <= 0:
            logger.info("No content in file ({}) for {}".format(filename, user_id))

        logger.info("Ingesting file ({}) for {}".format(filename, user_id))

        batch = []
        counter = 0
        batch_counter = 0
        batch_total = int(math.ceil(float(prospect_count) / self.batch_size))

        for prospect in content_data:
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
                batch = []
                logger.info("[RABBITCONN] - Batch message {} of {} for file {}".format(batch_counter, batch_total,
                                                                                       redis_key_root))
        logger.info('############### PROSPECT COUNT = {}'.format(str(prospect_count)))

    @staticmethod
    def _get_queue_replica_topic(queue_replicas, base_routine_key, ingestion_queue):
        # get first replica stats
        rabbit_url = 'http://{}:{}/api/queues/{}/{}-{}'.format(RABBIT_MGT_HOST, str(RABBIT_MGT_PORT), RABBIT_VHOST,
                                                               ingestion_queue, '0')

        print("***rabbit_url:")
        print(rabbit_url)
        print("***RABBIT_MGT_HOST:")
        print(RABBIT_MGT_HOST)
        print("***RABBIT_MGT_PORT:")
        print(RABBIT_MGT_PORT)
        print("***RABBIT_VHOST:")
        print(RABBIT_VHOST)

        req = requests.get(url=rabbit_url, auth=(RABBIT_USER, RABBIT_PASS))

        print("***req.text:")
        print(req.text)

        message_len = json.loads(req.text).get('messages')

        print("***message_len:")
        print(message_len)

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
