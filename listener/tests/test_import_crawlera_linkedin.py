import json
from unittest.mock import Mock, patch, sentinel, call
import pytest

from listener.import_crawlera_linkedin import IngestCrawleraLinkedin
from common_configs.google_storage import STORAGE_CRAWLERA_LINKEDIN_FOLDER, STORAGE_CRAWLERA_LINKEDIN_BUCKET
from common_configs.queue import UPLOAD_CRAWLERA_LINKEDIN_BATCH


@pytest.fixture(scope="function")
def fixt_class():
    return IngestCrawleraLinkedin()


@pytest.fixture(scope='function')
def fixt_body():
    return json.dumps({
        'filename': '{}foo_filename'.format(STORAGE_CRAWLERA_LINKEDIN_FOLDER),
    }).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_content_data_with_prospects():
    return '\n'.join(
        '{"foo%d": "bar%d"}' % (i, i)
        for i in range(10)
    ).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_content_data_without_prospects():
    return ''.encode('utf-8')


@patch('listener.import_crawlera_linkedin.IngestionTask')
@patch('listener.import_crawlera_linkedin.gzip')
@patch('listener.import_crawlera_linkedin.logger')
def test_listen_without_prospects(mock_logger, mock_gzip, mock_ingestion_task,
                                  fixt_content_data_without_prospects, fixt_body, fixt_class):
    mock_info = mock_logger.info
    mock_gzip.decompress.return_value = fixt_content_data_without_prospects
    fixt_class._get_google_storage_file = Mock(return_value=None)

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
    fixt_class._get_google_storage_file.assert_called_with(STORAGE_CRAWLERA_LINKEDIN_BUCKET,
                                                           '{}foo_filename'.format(STORAGE_CRAWLERA_LINKEDIN_FOLDER))
    mock_gzip.decompress.assert_called_with(None)
    mock_info.assert_has_calls([
        call('No content in file (linkedin/peoplefoo_filename)'),
        call('Ingesting file linkedin/peoplefoo_filename with 0 prospects'),
    ])


@patch('listener.import_crawlera_linkedin.MessageBus')
@patch('listener.import_crawlera_linkedin.IngestionTask')
@patch('listener.import_crawlera_linkedin.gzip')
@patch('listener.import_crawlera_linkedin.logger')
def test_listen_with_prospects(mock_logger, mock_gzip, mock_ingestion_task, mock_message_bus,
                               fixt_content_data_with_prospects, fixt_body, fixt_class):
    mock_info = mock_logger.info
    mock_gzip.decompress.return_value = fixt_content_data_with_prospects
    fixt_class._get_google_storage_file = Mock(return_value=None)
    mock_send = mock_message_bus.return_value.send

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)

    fixt_class._get_google_storage_file.assert_called_with(STORAGE_CRAWLERA_LINKEDIN_BUCKET,
                                                           '{}foo_filename'.format(STORAGE_CRAWLERA_LINKEDIN_FOLDER))
    mock_info.assert_has_calls([
        call('Ingesting file linkedin/peoplefoo_filename with 10 prospects'),
        call('[RABBITCONN] - Batch message 1 of 2 for file foo_filename'),
        call('[RABBITCONN] - Batch message 2 of 2 for file foo_filename'),
    ])

    mock_send.assert_has_calls([
        call(UPLOAD_CRAWLERA_LINKEDIN_BATCH, json.dumps({
            'redis_key_root': 'foo_filename',
            'prospects': (fixt_content_data_with_prospects.decode('utf-8').split("\n"))[:5],
            'batch_counter': 1,
            'batch_total': 2,
        }, sort_keys=True)),
        call(UPLOAD_CRAWLERA_LINKEDIN_BATCH, json.dumps({
            'redis_key_root': 'foo_filename',
            'prospects': (fixt_content_data_with_prospects.decode('utf-8').split("\n"))[5:10],
            'batch_counter': 2,
            'batch_total': 2,
        }, sort_keys=True))
    ])


@patch('listener.import_crawlera_linkedin.open')
@patch('listener.import_crawlera_linkedin.env')
@patch('listener.import_crawlera_linkedin.json')
@patch('listener.import_crawlera_linkedin.GoogleStorage')
def test_get_google_storage_file_with_credentials(mock_google_storage, mock_json, mock_env, mock_open, fixt_class):
    mock_env.is_local.return_value = True
    mock_json.load.return_value = sentinel.credentials
    mock_get_file = mock_google_storage.return_value.get_file

    fixt_class._get_google_storage_file(sentinel.bucket, sentinel.filename)
    mock_google_storage.assert_called_with(sentinel.credentials)
    mock_get_file.assert_called_with(sentinel.bucket, sentinel.filename)


# @patch('listener.import_crawlera_linkedin.env')
# @patch('listener.import_crawlera_linkedin.GoogleStorage')
# def test_get_google_storage_file_without_credentials(mock_google_storage, mock_env, fixt_class):
#     mock_get_file = mock_google_storage.return_value.get_file
#     # mock_env.is_local.return_value = False
#     fixt_class._get_google_storage_file(sentinel.bucket, sentinel.filename)
#     mock_google_storage.assert_called_with(None)
#     mock_get_file.assert_called_with(sentinel.bucket, sentinel.filename)
