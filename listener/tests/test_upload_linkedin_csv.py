import csv
import json
from unittest.mock import patch, sentinel, Mock, call
import pytest

from listener.upload_linkedin_csv import IngestLinkedinCSV
from common_configs.google_storage import STORAGE_USER_BUCKET, STORAGE_LINKEDIN_FOLDER
from common_configs.queue import UPLOAD_LINKEDIN_BATCH


@pytest.fixture(scope="function")
def fixt_class():
    return IngestLinkedinCSV()


@pytest.fixture(scope='function')
def fixt_body():
    return json.dumps({
        'filename': '{}/foo_filename'.format(STORAGE_LINKEDIN_FOLDER),
        'user_id': 'foo_user_id',
    }).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_data_with_prospect():
    return ('foo\n' + '\n'.join(
        'bar%d' % i
        for i in range(10)
    )).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_data_without_prospect():
    return ''.encode('utf-8')


@patch('listener.upload_linkedin_csv.logger')
def test_listen_without_prospects(mock_logger, fixt_body, fixt_data_without_prospect, fixt_class):
    mock_info = mock_logger.info
    fixt_class._get_csv_from_google_storage = Mock(return_value=fixt_data_without_prospect)

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
    fixt_class._get_csv_from_google_storage.assert_called_with('{}/foo_filename'.format(STORAGE_LINKEDIN_FOLDER))
    mock_info.assert_called_once_with('Ingesting file (linkedin/foo_filename) for foo_user_id')


@patch('listener.upload_linkedin_csv.MessageBus')
@patch('listener.upload_linkedin_csv.logger')
def test_listen_with_prospect(mock_logger, mock_message_bus, fixt_body, fixt_data_with_prospect, fixt_class):
    mock_info = mock_logger.info
    fixt_class._get_csv_from_google_storage = Mock(return_value=fixt_data_with_prospect)
    mock_send = mock_message_bus.return_value.send

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
    fixt_class._get_csv_from_google_storage.assert_called_with('linkedin/foo_filename')
    mock_info.assert_has_calls([
        call('Ingesting file (linkedin/foo_filename) for foo_user_id'),
        call('[RABBITCONN] - Batch message 1 of 2 for file foo_filename'),
        call('[RABBITCONN] - Batch message 2 of 2 for file foo_filename'),
    ])
    # mock_send.assert_has_calls([
    #     call(UPLOAD_LINKEDIN_BATCH, json.dumps({
    #         "redis_key_root": 'foo_filename',
    #         "user_id": 'foo_user_id',
    #         "prospects": list(csv.DictReader(fixt_data_with_prospect.decode('utf-8', 'replace').splitlines()))[:5],
    #         "batch_counter": 1,
    #         "batch_total": 2
    #     }, sort_keys=True)),
    #     call(UPLOAD_LINKEDIN_BATCH, json.dumps({
    #         "redis_key_root": 'foo_filename',
    #         "user_id": 'foo_user_id',
    #         "prospects": list(csv.DictReader(fixt_data_with_prospect.decode('utf-8', 'replace').splitlines()))[5:10],
    #         "batch_counter": 2,
    #         "batch_total": 2
    #     }, sort_keys=True))
    # ])

@patch('listener.upload_linkedin_csv.GoogleStorage')
@patch('listener.upload_linkedin_csv.env')
@patch('listener.upload_linkedin_csv.json')
@patch('listener.upload_linkedin_csv.open')
def test_get_csv_from_google_storage_with_credentials(mock_open, mock_json, mock_env, mock_google_storage, fixt_class):
    mock_env.is_local.return_value = True
    mock_json.load.return_value = 'foo'
    mock_get_file = mock_google_storage.return_value.get_file

    fixt_class._get_csv_from_google_storage(sentinel.filename)
    mock_google_storage.assert_called_with('foo')
    mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)


# @patch('listener.upload_linkedin_csv.GoogleStorage')
# @patch('listener.upload_linkedin_csv.env')
# def test_get_csv_from_google_storage_without_credentials(mock_env, mock_google_storage, fixt_class):
#     mock_env.is_local.return_value = False
#     mock_get_file = mock_google_storage.return_value.get_file
#
#     fixt_class._get_csv_from_google_storage(sentinel.filename)
#     mock_google_storage.assert_called_with(None)
#     mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)
