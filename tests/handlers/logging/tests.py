import logging
import sys
from unittest2 import TestCase
from raven.base import Client
from raven.handlers.logging import SentryHandler
from raven.utils.stacks import iter_stack_frames


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class LoggingIntegrationTest(TestCase):
    def setUp(self):
        self.client = TempStoreClient(include_paths=['tests', 'raven'])
        self.handler = SentryHandler(self.client)

    def make_record(self, msg, args=(), level=logging.INFO, extra=None, exc_info=None):
        record = logging.LogRecord('root', level, __file__, 27, msg, args, exc_info, 'make_record')
        if extra:
            for key, value in extra.iteritems():
                record.__dict__[key] = value
        return record

    def test_logger_basic(self):
        record = self.make_record('This is a test error')
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['logger'], 'root')
        self.assertEquals(event['level'], logging.INFO)
        self.assertEquals(event['message'], 'This is a test error')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test error')
        self.assertEquals(msg['params'], ())

    def test_logger_extra_data(self):
        record = self.make_record('This is a test error', extra={'data': {
            'url': 'http://example.com',
        }})
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['extra']['url'], 'http://example.com')

    def test_logger_exc_info(self):
        try:
            raise ValueError('This is a test ValueError')
        except ValueError:
            record = self.make_record('This is a test info with an exception', exc_info=sys.exc_info())
        else:
            self.fail('Should have raised an exception')

        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)

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

    def test_message_params(self):
        record = self.make_record('This is a test of %s', args=('args',))
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'This is a test of args')
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test of %s')
        self.assertEquals(msg['params'], ('args',))

    def test_record_stack(self):
        record = self.make_record('This is a test of stacks', extra={'stack': True})
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        frames = event['sentry.interfaces.Stacktrace']['frames']
        self.assertNotEquals(len(frames), 1)
        frame = frames[0]
        self.assertEquals(frame['module'], 'raven.handlers.logging')
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        self.assertEquals(event['culprit'], 'root in make_record')
        self.assertEquals(event['message'], 'This is a test of stacks')

    def test_no_record_stack(self):
        record = self.make_record('This is a test with no stacks', extra={'stack': False})
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'This is a test with no stacks')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)

    def test_explicit_stack(self):
        record = self.make_record('This is a test of stacks', extra={'stack': iter_stack_frames()})
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        assert 'sentry.interfaces.Stacktrace' in event
        assert 'culprit' in event
        assert event['culprit'] == 'root in make_record'
        self.assertTrue('message' in event, event)
        self.assertEquals(event['message'], 'This is a test of stacks')
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEquals(msg['message'], 'This is a test of stacks')
        self.assertEquals(msg['params'], ())

    def test_extra_culprit(self):
        record = self.make_record('This is a test of stacks', extra={'culprit': 'foo in bar'})
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['culprit'], 'foo in bar')

    def test_extra_data_as_string(self):
        record = self.make_record('Message', extra={'data': 'foo'})
        self.handler.emit(record)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['extra']['data'], 'foo')


class LoggingHandlerTest(TestCase):
    def test_client_arg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)
        self.assertEquals(handler.client, client)

    def test_client_kwarg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client=client)
        self.assertEquals(handler.client, client)

    def test_args_as_servers_and_key(self):
        handler = SentryHandler(['http://sentry.local/api/store/'], 'KEY')
        self.assertTrue(isinstance(handler.client, Client))

    def test_first_arg_as_dsn(self):
        handler = SentryHandler('http://public:secret@example.com/1')
        self.assertTrue(isinstance(handler.client, Client))

    def test_custom_client_class(self):
        handler = SentryHandler('http://public:secret@example.com/1', client_cls=TempStoreClient)
        self.assertTrue(type(handler.client), TempStoreClient)

    def test_invalid_first_arg_type(self):
        self.assertRaises(ValueError, SentryHandler, object)

    def test_logging_level_set(self):
        handler = SentryHandler('http://public:secret@example.com/1', level="ERROR")
        # XXX: some version of python 2.6 seem to pass the string on instead of coercing it
        self.assertTrue(handler.level in (logging.ERROR, 'ERROR'))

    def test_logging_level_not_set(self):
        handler = SentryHandler('http://public:secret@example.com/1')
        self.assertEquals(handler.level, logging.NOTSET)
