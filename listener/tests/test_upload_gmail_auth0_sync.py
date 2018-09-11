import json
from unittest.mock import patch, sentinel, Mock, call
import pytest

from listener.upload_gmail_auth0_sync import IngestGmailAuth0Sync
from common_configs.google_storage import STORAGE_USER_BUCKET, STORAGE_GMAIL_AUTH0_SYNC_FOLDER
from common_configs.queue import UPLOAD_GMAIL_AUTH0_SYNC_BATCH

# @pytest.fixture(scope="module")
# def fixt_adapter():
#     return IngestGmailAuth0Sync()



@pytest.fixture(scope="function")
def fixt_class():
    return IngestGmailAuth0Sync()


@pytest.fixture(scope='function')
def fixt_body():
    return json.dumps({
        'filename': '{}/foo_filename'.format(STORAGE_GMAIL_AUTH0_SYNC_FOLDER),
        'user_id': 'foo_user_id',
    }).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_file_content_with_content():
    return [
        {
            'foo%d' % i: 'bar%d' % i,
        }
        for i in range(10)
    ]


@pytest.fixture(scope='function')
def fixt_file_content_without_content():
    return json.dumps([]).encode('utf-8')


@patch('listener.upload_gmail_auth0_sync.MessageBus')
@patch('listener.upload_gmail_auth0_sync.IngestionTask')
@patch('listener.upload_gmail_auth0_sync.logger')
def test_listen_with_content(mock_logger, mock_ingestion_task, mock_message_bus, fixt_body,
                             fixt_file_content_with_content, fixt_class):
    mock_info = mock_logger.info
    mock_send = mock_message_bus.return_value.send
    fixt_class._get_csv_from_google_storage = Mock(return_value=json.dumps(fixt_file_content_with_content).encode('utf-8'))

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)

    mock_info.assert_has_calls([
        call('Ingesting file (gmail_auth0_sync/foo_filename) for foo_user_id'),
        call('[RABBITCONN] - Batch message 1 of 2 for file gmail_auth0_sync.foo_filename'),
        call('[RABBITCONN] - Batch message 2 of 2 for file gmail_auth0_sync.foo_filename')
    ])
    assert mock_send.call_count == 2
    # mock_send.assert_has_calls([
    #     call(UPLOAD_GMAIL_AUTH0_SYNC_BATCH, json.dumps({
    #         "redis_key_root": 'foo_filename',
    #         "user_id": 'foo_user_id',
    #         "prospects": fixt_file_content_with_content[:5],
    #         "batch_counter": 1,
    #         "batch_total": 2,
    #     }, sort_keys=True)),
    #     call(UPLOAD_GMAIL_AUTH0_SYNC_BATCH, json.dumps({
    #         "redis_key_root": 'foo_filename',
    #         "user_id": 'foo_user_id',
    #         "prospects": fixt_file_content_with_content[5:10],
    #         "batch_counter": 2,
    #         "batch_total": 2,
    #     }, sort_keys=True)),
    # ])


@patch('listener.upload_gmail_auth0_sync.IngestionTask')
@patch('listener.upload_gmail_auth0_sync.logger')
def test_listen_without_content(mock_logger, mock_ingestion_task, fixt_body, fixt_file_content_without_content,
                                fixt_class):
    mock_info = mock_logger.info
    fixt_class._get_csv_from_google_storage = Mock(return_value=fixt_file_content_without_content)

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)

    mock_info.assert_has_calls([
        call('No content in file ({}/foo_filename) for foo_user_id'.format(STORAGE_GMAIL_AUTH0_SYNC_FOLDER)),
        call('Ingesting file ({}/foo_filename) for foo_user_id'.format(STORAGE_GMAIL_AUTH0_SYNC_FOLDER)),
    ])


# @patch('listener.upload_gmail_auth0_sync.env')
# @patch('listener.upload_gmail_auth0_sync.GoogleStorage')
# def test_get_csv_from_google_storage_without_credentials(mock_google_storage, mock_env, fixt_class):
#     mock_get_file = mock_google_storage.return_value.get_file
#     mock_env.is_local.return_value = False
#
#     fixt_class._get_csv_from_google_storage(sentinel.filename)
#     mock_google_storage.assert_called_with(None)
#     mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)


@patch('listener.upload_gmail_auth0_sync.json')
@patch('listener.upload_gmail_auth0_sync.env')
@patch('listener.upload_gmail_auth0_sync.GoogleStorage')
@patch('listener.upload_gmail_auth0_sync.open')
def test_get_csv_from_google_storage_with_credentials(mock_open_file, mock_google_storage, mock_env, mock_json,
                                                      fixt_class):
    mock_env.is_local.return_value = True
    mock_json.load.return_value = 'foo'
    mock_get_file = mock_google_storage.return_value.get_file

    fixt_class._get_csv_from_google_storage(sentinel.filename)
    mock_google_storage.assert_called_with('foo')
    mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)
