import json
import logging
import math
import os
import zipfile
from csv import DictReader
from shutil import rmtree
from tempfile import mkdtemp
import requests

from common_configs.aws_storage import AwsStorage, STORAGE_USER_BUCKET
from common_configs.listener.resource import Resource
from common_configs.message_bus import MessageBus
from common_configs.queue import UPLOAD_LINKEDIN_BATCH

from common_configs.service import RABBIT_MGT_HOST, RABBIT_MGT_PORT, RABBIT_VHOST, RABBIT_USER, RABBIT_PASS, \
    SVC_INGESTION_QUEUE
from conf.config import RABBIT_INGESTION_REPLICAS
# from ingestion.ingestion_task import IngestionTask
# import time
# import random
# from common_configs import env


logger = logging.getLogger("service_ingestion_logger")


class IngestLinkedinZip(Resource):
    batch_size = 5
    storage = AwsStorage()

    def listen(self, ch, method, properties, body):
        data = json.loads(body.decode('utf-8'))

        if RABBIT_INGESTION_REPLICAS:
            routing_key = self._get_queue_replica_topic(RABBIT_INGESTION_REPLICAS,
                                                        UPLOAD_LINKEDIN_BATCH,
                                                        SVC_INGESTION_QUEUE)
        else:
            routing_key = UPLOAD_LINKEDIN_BATCH

        tmp_path = mkdtemp()
        tmp_zip = os.path.join(tmp_path, 'tmp.zip')
        contacts_data_path = os.path.join(tmp_path, 'Contacts.csv')
        connections_data_path = os.path.join(tmp_path, 'Connections.csv')

        user_id = data['user_id']
        file_path = data['filename']
        filename = file_path.split('/')[-1]
        redis_key_root = file_path.replace("/", ".")

        logger.info(file_path)
        logger.info(tmp_zip)
        logger.info("Downloading zip file ({}) for {}".format(filename, user_id))

        self.storage.download_object(file_path, tmp_zip)
        logger.info("Extracting zip file ({}) for {}".format(filename, user_id))
        self._extract_zip(tmp_zip, tmp_path)

        try:
            connections_count = self._count_lines(connections_data_path)
            logger.info("Ingesting Connections file ({}) for {}".format(filename, user_id))
            connections_data = open(connections_data_path, "r", encoding="utf-8")
            self._publish_batches(connections_data,
                                  connections_count,
                                  redis_key_root.replace('linkedin', 'linkedin.connections'),
                                  user_id,
                                  'connections',
                                  routing_key)

        except Exception as e:
            logger.error(e)
            logger.info("No Connections file in {} for user {}".format(filename, user_id))

        try:
            contacts_count = self._count_lines(contacts_data_path)
            logger.info("Ingesting Contacts file ({}) for {}".format(filename, user_id))
            contacts_data = open(contacts_data_path, "r", encoding="utf-8")
            self._publish_batches(contacts_data,
                                  contacts_count,
                                  redis_key_root.replace('linkedin', 'linkedin.contacts'),
                                  user_id,
                                  'contacts',
                                  routing_key)
        except Exception as e:
            logger.error(e)
            logger.info("No Contacts file in {} for user {}".format(filename, user_id))

        rmtree(tmp_path)

    def _publish_batches(self, prospect_data, prospect_count, redis_key_root, user_id, filetype, routing_key):
        reader = DictReader(prospect_data)

        for data in self._generate_batches(reader, prospect_count, redis_key_root, user_id, filetype):
            MessageBus().send(routing_key, json.dumps(data, sort_keys=True))

    def _generate_batches(self, reader, prospect_count, redis_key_root, user_id, filetype):
        batch = []
        counter = 0
        batch_counter = 0
        batch_total = int(math.ceil(float(prospect_count) / self.batch_size))

        for prospect in reader:
            batch.append(prospect)
            counter += 1

            if counter % self.batch_size == 0 or counter == prospect_count:
                batch_counter += 1

                yield {
                    "redis_key_root": redis_key_root,
                    "user_id": user_id,
                    "prospects": batch,
                    "batch_counter": batch_counter,
                    "batch_total": batch_total,
                    "linkedin_file": filetype
                }

                logger.info("[RABBITCONN] - Batch message {} of {} for file {}".format(batch_counter, batch_total, redis_key_root))

                batch = []
        logger.info('############### PROSPECT COUNT = {}'.format(str(prospect_count)))

    @staticmethod
    def _get_queue_replica_topic(queue_replicas, base_routine_key, ingestion_queue):
        # get first replica stats
        rabbit_url = 'http://{}:{}/api/queues/{}/{}-{}'.format(RABBIT_MGT_HOST, str(RABBIT_MGT_PORT),
            RABBIT_VHOST.replace('/', '%2F'), ingestion_queue, '0')
        req = requests.get(url=rabbit_url, auth=(RABBIT_USER, RABBIT_PASS))
        message_len = json.loads(req.text).get('messages')

        if message_len == 0:
            return '{}-0'.format(base_routine_key)

        min_replica = {"replica": 0, "count": message_len}

        for replica in range(1, int(queue_replicas)):
            rabbit_url = 'http://{}:{}/api/queues/{}/{}-{}'.format(RABBIT_MGT_HOST, str(RABBIT_MGT_PORT),
                RABBIT_VHOST.replace('/', '%2F'), ingestion_queue, replica)
            req = requests.get(url=rabbit_url, auth=(RABBIT_USER, RABBIT_PASS))
            message_len = json.loads(req.text).get('messages')

            if message_len == 0:
                return '{}-{}'.format(base_routine_key, str(replica))

            if message_len < min_replica.get('count'):
                min_replica['replica'] = replica
                min_replica['count'] = message_len

        return '{}-{}'.format(base_routine_key, str(min_replica.get('replica')))

    @staticmethod
    def _extract_zip(src, dest):  # pragma: nocover
        with zipfile.ZipFile(src, 'r') as zf:
            zf.extractall(dest)

    @staticmethod
    def _count_lines(file):  # pragma: nocover
        # This gets a count -1 for header
        return sum(1 for _ in open(file)) - 1

    @staticmethod
    def _array_unique(seq, idfun=lambda x: x):
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            if marker in seen:
                continue
            seen[marker] = 1
            result.append(item)
        return result

    def _open_and_convert_file(self, path, prospect_data, linkedin_type):
        try:
            csv_data = open(path, "r", encoding="utf-8")
            reader = DictReader(csv_data)

            for prospect in reader:

                if prospect.get('PhoneNumbers') or prospect.get('PhoneNumbers') == '':
                    prospect['PhoneNumbers'] = prospect.get('PhoneNumbers').split(',')

                if prospect.get('EmailAddress') or prospect.get('EmailAddress') == '':
                    prospect['EmailAddress'] = prospect.get('EmailAddress').split(',')

                if prospect.get('Companies') or prospect.get('Companies') == '':
                    prospect['Company'] = prospect.pop('Companies')

                if prospect.get('Position') or prospect.get('Position') == '':
                    prospect['Title'] = prospect.pop('Position')

                if not prospect.get('FirstName') or not prospect.get('LastName'):
                    prospect_data.append(prospect)
                elif any(x for x in prospect_data if (x['FirstName'] == prospect.get('FirstName') and x['LastName'] == prospect.get('LastName'))):
                    for index, item in enumerate(prospect_data):
                        if item['FirstName'] == prospect.get('FirstName') and item['LastName'] == prospect.get('LastName') and item['Company'] == prospect.get('Company'):
                            break
                        else:
                            index = -1

                    if index > -1:
                        for field in prospect:
                            if not prospect_data[index].get(field):
                                prospect_data[index][field] = prospect.get(field)

                        if not prospect_data[index].get('linkedin_type'):
                            prospect_data[index]['linkedin_type'] = [linkedin_type]
                        else:
                            prospect_data[index]['linkedin_type'].append(linkedin_type)

                        if prospect.get('EmailAddress'):
                            if prospect_data[index]['EmailAddress'] == '':
                                prospect_data[index]['EmailAddress'] = []

                            prospect_data[index]['EmailAddress'] = self._array_unique(prospect_data[index]['EmailAddress'] + prospect.get('EmailAddress'))
                    else:
                        prospect['linkedin_type'] = [linkedin_type]
                        prospect_data.append(prospect)
                else:
                    prospect['linkedin_type'] = [linkedin_type]
                    prospect_data.append(prospect)

            csv_data.close()
            return prospect_data

        except Exception as e:
            logger.error("Error pulling {}\nError: {}".format(path, e))
            return prospect_data