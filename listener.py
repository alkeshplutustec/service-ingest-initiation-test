# coding=utf-8
import logging

from common_configs.logger.common_configs_logger import CommonConfigsLogger
from common_configs.logger.logger_file_handler import LoggerFileHandler
from gevent import monkey
from common_configs.listener.listener import Listener

from common_configs.queue import \
    UPLOAD_LINKEDIN_CSV, UPLOAD_LINKEDIN_ZIP, UPLOAD_CLOUDSPONGE, \
    UPLOAD_IPHONE_ADDRESSBOOK, UPLOAD_CRAWLERA_LINKEDIN, UPLOAD_GMAIL_AUTH0_SYNC, \
    UPLOAD_YAHOO_AUTH0_SYNC, UPLOAD_AGENT_LIST

from listener.import_crawlera_linkedin import IngestCrawleraLinkedin
from listener.upload_cloudsponge import IngestCloudSponge
from listener.upload_gmail_auth0_sync import IngestGmailAuth0Sync
from listener.upload_yahoo_auth0_sync import IngestYahooAuth0Sync
from listener.upload_iphone_addressbook import IngestIPhoneAddressBook
from listener.upload_linkedin_csv import IngestLinkedinCSV
from listener.upload_linkedin_zip import IngestLinkedinZip
from listener.upload_agent_list import IngestAgentList

# from common_configs.env import is_demo, is_prod
# from conf.config import SENTRY_API_KEY_URL

# monkey.patch_all()

# from raven import Client

# if is_demo() or is_prod():
#     client = Client(SENTRY_API_KEY_URL)

# Setup common configs log handler
CommonConfigsLogger.set_common_configs_logger(service_tag="SERVICE INGESTION")

# Create and add app (service processing) log handler
app_logger = logging.getLogger("service_ingest_intiation_logger")
app_file_handler = LoggerFileHandler.create_logger_file_handler(service_tag="[SERVICE INGEST INITIATION]",
                                                                logger_filename="application.log")

app_logger.addHandler(app_file_handler)

listener = Listener()
listener.add_resource(IngestCrawleraLinkedin, UPLOAD_CRAWLERA_LINKEDIN)
listener.add_resource(IngestLinkedinCSV, UPLOAD_LINKEDIN_CSV)
listener.add_resource(IngestLinkedinZip, UPLOAD_LINKEDIN_ZIP)
listener.add_resource(IngestCloudSponge, UPLOAD_CLOUDSPONGE)
listener.add_resource(IngestIPhoneAddressBook, UPLOAD_IPHONE_ADDRESSBOOK)
listener.add_resource(IngestGmailAuth0Sync, UPLOAD_GMAIL_AUTH0_SYNC)
listener.add_resource(IngestYahooAuth0Sync, UPLOAD_YAHOO_AUTH0_SYNC)
listener.add_resource(IngestAgentList, UPLOAD_AGENT_LIST)

if __name__ == '__main__':
    listener.run()
