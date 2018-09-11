import gzip
import json
import logging
import math

from common_configs import env
from common_configs.aws_storage import AwsStorage, STORAGE_CRAWLERA_LINKEDIN_FOLDER
from common_configs.listener.resource import Resource
from common_configs.message_bus import MessageBus
from common_configs.queue import UPLOAD_CRAWLERA_LINKEDIN_BATCH

from ingestion.ingestion_task import IngestionTask

logger = logging.getLogger("service_ingestion_logger")


class IngestCrawleraLinkedin(Resource):
    def __init__(self):
        batch_size = 5
        storage = AwsStorage(STORAGE_USER_BUCKET)

    def listen(self, ch, method, properties, body):
        data = json.loads(body.decode('utf-8'))

        filename = data.get('filename')
        redis_key_root = filename.replace(STORAGE_CRAWLERA_LINKEDIN_FOLDER, "")

        gz_file_content = self.storage.get_file(filename)
        # may need to rework
        
         # gz decompress it
        file_content = gzip.decompress(gz_file_content)

        # split the json lines
        content_data = file_content.decode("utf-8").split("\n")
        prospect_count = len(content_data)
        if content_data == [""]:
            prospect_count = 0

        if prospect_count <= 0:
            logger.info("No content in file ({})".format(filename))

        logger.info("Ingesting file {} with {} prospects".format(filename, prospect_count))

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
                    "prospects": batch,
                    "batch_counter": batch_counter,
                    "batch_total": batch_total
                }

                MessageBus().send(UPLOAD_CRAWLERA_LINKEDIN_BATCH, json.dumps(data, sort_keys=True))
                logger.info("[RABBITCONN] - Batch message {} of {} for file {}".format(batch_counter, batch_total,
                                                                                       redis_key_root))
                batch = []
