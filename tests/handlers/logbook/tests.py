from __future__ import with_statement
from __future__ import unicode_literals

import logbook
import pytest
from raven.utils.testutils import TestCase
from raven.utils import six
from raven.base import Client
from raven.handlers.logbook import SentryHandler


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class LogbookHandlerTest(TestCase):
    def setUp(self):
        self.logger = logbook.Logger(__name__)

    def test_logger(self):
        client = TempStoreClient(include_paths=['tests', 'raven'])
        handler = SentryHandler(client)
        logger = self.logger

        with handler.applicationbound():
            logger.error('This is a test error')

            assert len(client.events) == 1
            event = client.events.pop(0)
            assert event['logger'] == __name__
            assert event['level'] == 'error'
            assert event['message'] == 'This is a test error'
            assert 'sentry.interfaces.Stacktrace' not in event
            assert 'sentry.interfaces.Exception' not in event
            assert 'sentry.interfaces.Message' in event
            msg = event['sentry.interfaces.Message']
            assert msg['message'] == 'This is a test error'
            assert msg['params'] == ()

            logger.warning('This is a test warning')
            assert len(client.events) == 1
            event = client.events.pop(0)
            assert event['logger'] == __name__
            assert event['level'] == 'warning'
            assert event['message'] == 'This is a test warning'
            assert 'sentry.interfaces.Stacktrace' not in event
            assert 'sentry.interfaces.Exception' not in event
            assert 'sentry.interfaces.Message' in event
            msg = event['sentry.interfaces.Message']
            assert msg['message'] == 'This is a test warning'
            assert msg['params'] == ()

            logger.info('This is a test info with a url', extra=dict(
                url='http://example.com',
            ))
            assert len(client.events) == 1
            event = client.events.pop(0)
            if six.PY3:
                expected = "'http://example.com'"
            else:
                expected = "u'http://example.com'"
            assert event['extra']['url'] == expected
            assert 'sentry.interfaces.Stacktrace' not in event
            assert 'sentry.interfaces.Exception' not in event
            assert 'sentry.interfaces.Message' in event
            msg = event['sentry.interfaces.Message']
            assert msg['message'] == 'This is a test info with a url'
            assert msg['params'] == ()

            try:
                raise ValueError('This is a test ValueError')
            except ValueError:
                logger.info('This is a test info with an exception', exc_info=True)

            assert len(client.events) == 1
            event = client.events.pop(0)

            assert event['message'] == 'This is a test info with an exception'
            assert 'sentry.interfaces.Stacktrace' in event
            assert 'sentry.interfaces.Exception' in event
            exc = event['sentry.interfaces.Exception']
            assert exc['type'] == 'ValueError'
            assert exc['value'] == 'This is a test ValueError'
            assert 'sentry.interfaces.Message' in event
            msg = event['sentry.interfaces.Message']
            assert msg['message'] == 'This is a test info with an exception'
            assert msg['params'] == ()

            # test args
            logger.info('This is a test of {0}', 'args')
            assert len(client.events) == 1
            event = client.events.pop(0)
            assert event['message'] == 'This is a test of args'
            assert 'sentry.interfaces.Stacktrace' not in event
            assert 'sentry.interfaces.Exception' not in event
            assert 'sentry.interfaces.Message' in event
            msg = event['sentry.interfaces.Message']
            assert msg['message'] == 'This is a test of {0}'
            expected = ("'args'",) if six.PY3 else ("u'args'",)
            assert msg['params'] == expected

    def test_client_arg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)
        assert handler.client == client

    def test_client_kwarg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client=client)
        assert handler.client == client

    def test_first_arg_as_dsn(self):
        handler = SentryHandler('http://public:secret@example.com/1')
        assert isinstance(handler.client, Client)

    def test_custom_client_class(self):
        handler = SentryHandler('http://public:secret@example.com/1', client_cls=TempStoreClient)
        assert type(handler.client) == TempStoreClient

    def test_invalid_first_arg_type(self):
        with pytest.raises(ValueError):
            SentryHandler(object)

    def test_missing_client_arg(self):
        with pytest.raises(TypeError):
            SentryHandler()
