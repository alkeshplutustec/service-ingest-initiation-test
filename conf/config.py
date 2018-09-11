import os
import ast

RABBIT_INGESTION_REPLICAS = os.getenv('RABBIT_INGESTION_REPLICAS')
if RABBIT_INGESTION_REPLICAS:
    RABBIT_INGESTION_REPLICAS = int(RABBIT_INGESTION_REPLICAS)

from common_configs.service import SVC_INGEST_INITIATION_QUEUE as RABBIT_QUEUE

GC_PROJECT = os.getenv('GC_PROJECT', 'advisorconnect-1238')

# SENTRY_API_KEY_URL = os.getenv('SENTRY_API_KEY_URL', '')

# ERS_FULLCONTACT     = ast.literal_eval(os.getenv('ERS_FULLCONTACT', 'True'))
# ERS_PIPL            = ast.literal_eval(os.getenv('ERS_PIPL', 'False'))
# ERS_NEXTCALLER      = ast.literal_eval(os.getenv('ERS_NEXTCALLER', 'True'))
# ERS_FORCE           = ast.literal_eval(os.getenv('ERS_FORCE', 'False'))
# ERS_MACROMEASURES   = os.getenv('ERS_MACROMEASURES', 'false')