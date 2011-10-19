import logging
from unittest2 import TestCase
from raven.base import Client
from raven.handlers.logging import SentryHandler

class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)

class LoggingHandlerTest(TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)

    def test_logger(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)

        logger = self.logger
        logger.handlers = []
        logger.addHandler(handler)

        logger.error('This is a test error')

        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['logger'], __name__)
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'This is a test error')
        self.assertFalse('frames' in event['data']['__sentry__'])

        logger.warning('This is a test warning')
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['logger'], __name__)
        self.assertEquals(event['level'], logging.WARNING)
        self.assertEquals(event['message'], 'This is a test warning')
        self.assertFalse('frames' in event['data']['__sentry__'])

        logger.info('This is a test info with a url', extra=dict(url='http://example.com'))
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['url'], 'http://example.com')
        self.assertFalse('frames' in event['data']['__sentry__'])

        try:
            raise ValueError('This is a test ValueError')
        except ValueError:
            logger.info('This is a test info with an exception', exc_info=True)

        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)

        self.assertEquals(event['class_name'], 'ValueError')
        self.assertEquals(event['message'], 'This is a test info with an exception')
        self.assertTrue('__sentry__' in event['data'])
        self.assertTrue('exception' in event['data']['__sentry__'])
        self.assertTrue('frames' in event['data']['__sentry__'])

        # test stacks
        logger.info('This is a test of stacks', extra={'stack': True})
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['view'], 'tests.handlers.tests.test_logger')
        self.assertEquals(event['message'], 'This is a test of stacks')
        self.assertTrue('__sentry__' in event['data'])
        self.assertTrue('frames' in event['data']['__sentry__'])

        # test no stacks
        logger.info('This is a test of no stacks', extra={'stack': False})
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['view'], None)
        self.assertEquals(event['message'], 'This is a test of no stacks')
        self.assertTrue('__sentry__' in event['data'])
        self.assertFalse('frames' in event['data']['__sentry__'])

    def test_init(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)
        assert handler.client == client

        handler = SentryHandler(client=client)
        assert handler.client == client

        handler = SentryHandler(['http://sentry.local/store/'], 'KEY')
        assert handler.client
