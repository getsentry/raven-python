import logging
from unittest2 import TestCase
from raven.base import Client
from raven.handlers.logging import SentryHandler
from raven.utils.stacks import iter_stack_frames

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
        client = TempStoreClient(include_paths=['tests', 'raven'])
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
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test error')
        self.assertEquals(msg['params'], ())

        logger.warning('This is a test warning')
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['logger'], __name__)
        self.assertEquals(event['level'], logging.WARNING)
        self.assertEquals(event['message'], 'This is a test warning')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test warning')
        self.assertEquals(msg['params'], ())

        logger.info('This is a test info with a url', extra=dict(
            data=dict(
                url='http://example.com',
            ),
        ))
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['extra']['url'], 'http://example.com')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test info with a url')
        self.assertEquals(msg['params'], ())

        try:
            raise ValueError('This is a test ValueError')
        except ValueError:
            logger.info('This is a test info with an exception', exc_info=True)

        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)

        self.assertEquals(event['message'], 'This is a test info with an exception')
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'This is a test ValueError')
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test info with an exception')
        self.assertEquals(msg['params'], ())

        # test stacks
        logger.info('This is a test of stacks', extra={'stack': True})
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        frames = event['sentry.interfaces.Stacktrace']['frames']
        self.assertNotEquals(len(frames), 1)
        frame = frames[0]
        self.assertEquals(frame['module'], __name__)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test of stacks')
        self.assertEquals(msg['params'], ())
        self.assertEquals(event['culprit'], 'tests.handlers.tests.test_logger')
        self.assertEquals(event['message'], 'This is a test of stacks')

        # test no stacks
        logger.info('This is a test of no stacks', extra={'stack': False})
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event.get('culprit'), None)
        self.assertEquals(event['message'], 'This is a test of no stacks')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test of no stacks')
        self.assertEquals(msg['params'], ())

        # test args
        logger.info('This is a test of %s', 'args')
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['message'], 'This is a test of args')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test of %s')
        self.assertEquals(msg['params'], ('args',))

        # test explicit stack
        logger.info('This is a test of stacks', extra={'stack': iter_stack_frames()})
        self.assertEquals(len(client.events), 1)
        event = client.events.pop(0)
        self.assertEquals(event['culprit'], 'tests.handlers.tests.test_logger')
        self.assertEquals(event['message'], 'This is a test of stacks')
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test of stacks')
        self.assertEquals(msg['params'], ())
        self.assertTrue('sentry.interfaces.Stacktrace' in event)

    def test_init(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)
        assert handler.client == client

        handler = SentryHandler(client=client)
        assert handler.client == client

        handler = SentryHandler(['http://sentry.local/api/store/'], 'KEY')
        assert handler.client
