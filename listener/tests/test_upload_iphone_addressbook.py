import json
from unittest.mock import patch, sentinel, Mock, call

import pytest

from common_configs.google_storage import STORAGE_USER_BUCKET, STORAGE_IPHONE_ADDRESSBOOK_FOLDER
from listener.upload_iphone_addressbook import IngestIPhoneAddressBook
from common_configs.queue import UPLOAD_IPHONE_ADDRESSBOOK_BATCH


@pytest.fixture(scope="function")
def fixt_class():
    return IngestIPhoneAddressBook()


@pytest.fixture(scope='function')
def fixt_body():
    return json.dumps({
        'filename': '{}/foo_filename'.format(STORAGE_IPHONE_ADDRESSBOOK_FOLDER),
        'user_id': 'foo_user_id',
    }).encode('utf-8')


@pytest.fixture(scope='function')
def fixt_file_content_with_contacts():
    return {
        'contacts': [
            {
                'foo%d' % i: 'bar%d' % i,
            }
            for i in range(10)
        ]
    }


@pytest.fixture(scope='function')
def fixt_file_content_without_contacts():
    return json.dumps({
        'contacts': [],
    }).encode('utf-8')

# @patch('listener.upload_iphone_addressbook.logger')
# def test_listen_without_contacts(mock_logger, fixt_body, fixt_class, fixt_file_content_without_contacts):
#     mock_info = mock_logger.info
#     fixt_class._get_csv_from_google_storage = Mock(return_value=fixt_file_content_without_contacts)
#
#     fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
#     mock_info.assert_has_calls([
#         call('No content in file (iphone_addressbook/foo_filename) for foo_user_id'),
#         call('Ingesting file (iphone_addressbook/foo_filename) for foo_user_id')
#     ])
#
#
# @patch('listener.upload_iphone_addressbook.MessageBus')
# @patch('listener.upload_iphone_addressbook.logger')
# def test_listen_with_contacts(mock_logger, mock_message_bus, fixt_class, fixt_body, fixt_file_content_with_contacts):
#     mock_info = mock_logger.info
#     mock_send = mock_message_bus.return_value.send
#     fixt_class._get_csv_from_google_storage = Mock(return_value=json.dumps(fixt_file_content_with_contacts).encode('utf-8'))
#
#     fixt_class.listen(sentinel.ch, sentinel.method, sentinel.properties, fixt_body)
#     mock_info.assert_has_calls([
#         call('Ingesting file (iphone_addressbook/foo_filename) for foo_user_id'),
#         call('[RABBITCONN] - Batch message 1 of 2 for file foo_filename'),
#         call('[RABBITCONN] - Batch message 2 of 2 for file foo_filename')
#     ])
#     assert mock_send.call_count == 2
#     # mock_send.assert_has_calls([
#     #     call(
#     #         UPLOAD_IPHONE_ADDRESSBOOK_BATCH,
#     #         json.dumps({
#     #             "redis_key_root": 'foo_filename',
#     #             "user_id": 'foo_user_id',
#     #             "prospects": fixt_file_content_with_contacts['contacts'][:5],
#     #             "batch_counter": 1,
#     #             "batch_total": 2,
#     #         }, sort_keys=True)
#     #     ),
#     #     call(
#     #         UPLOAD_IPHONE_ADDRESSBOOK_BATCH,
#     #         json.dumps({
#     #             "redis_key_root": 'foo_filename',
#     #             "user_id": 'foo_user_id',
#     #             "prospects": fixt_file_content_with_contacts['contacts'][5:10],
#     #             "batch_counter": 2,
#     #             "batch_total": 2,
#     #         }, sort_keys=True)
#     #     )
#     # ])

@patch('listener.upload_iphone_addressbook.json')
@patch('listener.upload_iphone_addressbook.env')
@patch('listener.upload_iphone_addressbook.GoogleStorage')
@patch('listener.upload_iphone_addressbook.open')
def test_get_csv_from_google_storage_with_credentials(mock_open_file, mock_google_storage, mock_env, mock_json,
                                                      fixt_class):
    mock_env.is_local.return_value = True
    mock_json.load.return_value = 'foo'
    mock_get_file = mock_google_storage.return_value.get_file

    fixt_class._get_csv_from_google_storage(sentinel.filename)
    mock_google_storage.assert_called_with('foo')
    mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)


# @patch('listener.upload_iphone_addressbook.env')
# @patch('listener.upload_iphone_addressbook.GoogleStorage')
# def test_get_csv_from_google_storage_without_credentials(mock_google_storage, mock_env, fixt_class):
#     mock_env.is_local.return_value = False
#     mock_get_file = mock_google_storage.return_value.get_file
#
#     fixt_class._get_csv_from_google_storage(sentinel.filename)
#     mock_google_storage.assert_called_with(None)
#     mock_get_file.assert_called_with(STORAGE_USER_BUCKET, sentinel.filename)
