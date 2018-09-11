import json
from unittest.mock import patch, sentinel, Mock, call

import pytest

from common_configs.google_storage import STORAGE_USER_BUCKET
from common_configs.queue import UPLOAD_LINKEDIN_BATCH
from listener.upload_linkedin_zip import IngestLinkedinZip


@pytest.fixture(scope="function")
def fixt_class():
    return IngestLinkedinZip()


@pytest.fixture(scope='function')
def fixt_body():
    return json.dumps({
        'filename': 'linkedin/foo_filename',
        'user_id': 'foo_user_id',
    }).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_reader():
    return [
        {
            'foo%d' % i: 'bar%d' % i,
        }
        for i in range(10)
    ]


# @patch('listener.upload_linkedin_zip.logger')
# def test_generate_batches(mock_logger, fixt_reader, fixt_class):
#     mock_info = mock_logger.info
#
#     assert list(fixt_class._generate_batches(
#         fixt_reader,
#         len(fixt_reader),
#         sentinel.redis_key_root,
#         sentinel.user_id,
#     )) == [
#                {
#                    "redis_key_root": sentinel.redis_key_root,
#                    "user_id": sentinel.user_id,
#                    "prospects": fixt_reader[:50],
#                    "batch_counter": 1,
#                    "batch_total": 2,
#                },
#                {
#                    "redis_key_root": sentinel.redis_key_root,
#                    "user_id": sentinel.user_id,
#                    "prospects": fixt_reader[50:100],
#                    "batch_counter": 2,
#                    "batch_total": 2,
#                },
#            ]
#
#     fmt = "[RABBITCONN] - Batch message {} of {} for file {}"
#     assert mock_info.call_count == 2
#     mock_info.assert_has_calls([
#         call(fmt.format(1, 2, sentinel.redis_key_root)),
#         call(fmt.format(2, 2, sentinel.redis_key_root)),
#     ])


# @patch('listener.upload_linkedin_zip.DictReader', return_value=sentinel.csv_data)
# @patch('listener.upload_linkedin_zip.MessageBus')
# def test_publish_batches(mock_message_bus, mock_dict_reader, fixt_reader, fixt_class):
#     mock_send = mock_message_bus.return_value.send
#     fixt_class._generate_batches = Mock(return_value=["a", "b"])
#
#     fixt_class._publish_batches(sentinel.csv_data, sentinel.prospect_count, sentinel.redis_key_root, sentinel.user_id)
#
#     assert mock_send.call_count == 2
#
#     mock_send.assert_has_calls([
#         call(UPLOAD_LINKEDIN_BATCH, '"a"'),
#         call(UPLOAD_LINKEDIN_BATCH, '"b"'),
#     ])


# @patch('listener.upload_linkedin_zip.open')
# @patch('listener.upload_linkedin_zip.env')
# @patch('listener.upload_linkedin_zip.GoogleStorage')
# @patch('listener.upload_linkedin_zip.json')
# def test_download_file_from_google_storage_with_credentials(mock_json, mock_google_storage, mock_env, mock_open_file,
#                                                             fixt_class):
#     mock_env.is_local.return_value = True
#     mock_json.load.return_value = 'foo'
#     mock_download_object = mock_google_storage.return_value.download_object
#
#     fixt_class._download_file_from_google_storage(sentinel.filename, sentinel.out_file)
#     mock_google_storage.assert_called_with('foo')
#     mock_download_object.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename, sentinel.out_file)


# @patch('listener.upload_linkedin_zip.rmtree')
# @patch('listener.upload_linkedin_zip.logger')
# @patch('listener.upload_linkedin_zip.IngestionTask')
# @patch('listener.upload_linkedin_zip.mkdtemp', return_value="/tmp")
# @patch('builtins.open')
# def test_listen(mock_open, mock_mkdtemp, mock_ingestion_task, mock_logger, mock_rmtree, fixt_class, fixt_body):
#     fixt_class._count_lines = Mock(return_value=10)
#     fixt_class._extract_zip = Mock()
#     fixt_class._download_file_from_google_storage = Mock()
#     fixt_class._publish_batches = Mock()
#
#     fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
#
#     fixt_class._download_file_from_google_storage.assert_called_once_with('linkedin/foo_filename', '/tmp/tmp.zip')
#     fixt_class._extract_zip.assert_called_once_with('/tmp/tmp.zip', '/tmp')
#
#     calls = [
#         call("Downloading file (foo_filename) for foo_user_id"),
#         call("Ingesting file (foo_filename) for foo_user_id")]
#     mock_logger.info.assert_has_calls(calls)
#
#     fixt_class._publish_batches.assert_called_once_with([], 0, 'linkedin.foo_filename',
#                                                         'foo_user_id')
#
#     mock_open.return_value.close.assert_has_calls([call(), call()])
#     mock_rmtree.assert_called_once_with('/tmp')


# @patch('listener.upload_linkedin_zip.GoogleStorage')
# @patch('listener.upload_linkedin_zip.env')
# def test_download_file_from_google_storage_without_credentials(mock_env, mock_google_storage, fixt_class):
#     mock_env.is_local.return_value = False
#     mock_download_object = mock_google_storage.return_value.download_object
#     fixt_class._download_file_from_google_storage(sentinel.filename, sentinel.out_file)
#     mock_google_storage.assert_called_with(None)
#     mock_download_object.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename, sentinel.out_file)
