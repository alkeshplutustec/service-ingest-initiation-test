import json
from unittest.mock import patch, sentinel, Mock, call

import pytest

from common_configs.google_storage import STORAGE_CLOUDSPONGE_FOLDER
from common_configs.google_storage import STORAGE_USER_BUCKET
from common_configs.queue import UPLOAD_CLOUDSPONGE_BATCH
from listener.upload_cloudsponge import IngestCloudSponge


@pytest.fixture(scope="function")
def fixt_class():
    return IngestCloudSponge()


@pytest.fixture(scope='function')
def fixt_body():
    return json.dumps(
        {
            'filename': 'foo/filename',
            'user_id': 'foo_user_id'

        }
    ).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_content_data_with_prospects():
    return {
        'service': 'foo_service',
        'contacts': [
            {
                'foo%d' % i: 'bar%d' % i,
            }
            for i in range(10)
        ],
    }


@pytest.fixture(scope='function')
def fixt_content_data_without_prospects():
    return {
        'service': 'foo_service',
        'contacts': [],
    }


@patch('listener.upload_cloudsponge.logger')
def test_listen_without_prospects(mock_logger, fixt_class, fixt_body,
                                  fixt_content_data_without_prospects):
    mock_info = mock_logger.info
    fixt_class._get_csv_from_google_storage = Mock(
        return_value=json.dumps(fixt_content_data_without_prospects).encode('utf-8'))

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
    mock_info.assert_called_with(
        'Ingesting file ({}) for {}'.format('foo/filename', 'foo_user_id'))


@patch('listener.upload_cloudsponge.MessageBus')
@patch('listener.upload_cloudsponge.logger')
def test_listen_with_prospects(mock_logger, mock_message_bus, fixt_class, fixt_body, fixt_content_data_with_prospects):
    mock_info = mock_logger.info
    mock_send = mock_message_bus.return_value.send
    fixt_class._get_csv_from_google_storage = Mock(
        return_value=json.dumps(fixt_content_data_with_prospects).encode('utf-8'))

    fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)

    for prospect in fixt_content_data_with_prospects['contacts']:
        prospect.update({'_service': fixt_content_data_with_prospects['service']})

    mock_info.assert_has_calls([
        call('Ingesting file (foo/filename) for foo_user_id'),
        call('[RABBITCONN] - Batch message 1 of 2 for file foo.filename'),
        call('[RABBITCONN] - Batch message 2 of 2 for file foo.filename'),
    ])

    # assert mock_send.call_count == 2
    # mock_send.assert_has_calls([
    #     call(UPLOAD_CLOUDSPONGE_BATCH, json.dumps({
    #         'redis_key_root': 'foo.filename',
    #         'user_id': 'foo_user_id',
    #         'prospects': fixt_content_data_with_prospects['contacts'][:5],
    #         'batch_counter': 1,
    #         'batch_total': 2,
    #     }, sort_keys=True)),
    #     call(UPLOAD_CLOUDSPONGE_BATCH, json.dumps({
    #         'redis_key_root': 'foo.filename',
    #         'user_id': 'foo_user_id',
    #         'prospects': fixt_content_data_with_prospects['contacts'][5:10],
    #         'batch_counter': 2,
    #         'batch_total': 2,
    #     }, sort_keys=True))
    # ])


@patch('listener.upload_cloudsponge.json')
@patch('listener.upload_cloudsponge.env')
@patch('listener.upload_cloudsponge.GoogleStorage')
@patch('listener.upload_cloudsponge.open')
def test_get_csv_from_google_storage_with_credentials(mock_open_file, mock_google_storage, mock_env, mock_json,
                                                      fixt_class):
    mock_env.is_local.return_value = True
    mock_json.load.return_value = 'foo'
    mock_get_file = mock_google_storage.return_value.get_file

    fixt_class._get_csv_from_google_storage(sentinel.filename)
    mock_google_storage.assert_called_with('foo')
    mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)


# @patch('listener.upload_cloudsponge.env')
# @patch('listener.upload_cloudsponge.GoogleStorage')
# def test_get_csv_from_google_storage_without_credentials(mock_google_storage, mock_env, fixt_class):
#     mock_env.is_local.return_value = False
#     mock_get_file = mock_google_storage.return_value.get_file
#
#     fixt_class._get_csv_from_google_storage(sentinel.filename)
#     mock_google_storage.assert_called_with(None)
#     mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)

# def test_get_queue_replica_topic()
