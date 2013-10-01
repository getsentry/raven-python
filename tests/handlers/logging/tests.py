from __future__ import unicode_literals

import logging
import sys
from raven.utils.testutils import TestCase
from raven.utils import six
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

    def make_record(self, msg, args=(), level=logging.INFO, extra=None, exc_info=None, name='root', pathname=__file__):
        record = logging.LogRecord(name, level, pathname, 27, msg, args, exc_info, 'make_record')
        if extra:
            for key, value in six.iteritems(extra):
                record.__dict__[key] = value
        return record

    def test_logger_basic(self):
        record = self.make_record('This is a test error')
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEqual(event['logger'], 'root')
        self.assertEqual(event['level'], logging.INFO)
        self.assertEqual(event['message'], 'This is a test error')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEqual(msg['message'], 'This is a test error')
        self.assertEqual(msg['params'], ())

    def test_can_record(self):
        tests = [
            ("raven", False),
            ("raven.foo", False),
            ("sentry.errors", False),
            ("sentry.errors.foo", False),
            ("raven_utils", True),
        ]

        for test in tests:
            record = self.make_record("Test", name=test[0])
            self.assertEqual(self.handler.can_record(record), test[1])

    def test_logger_extra_data(self):
        record = self.make_record('This is a test error', extra={'data': {
            'url': 'http://example.com',
        }})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        if six.PY3:
            expected = "'http://example.com'"
        else:
            expected = "u'http://example.com'"
        self.assertEqual(event['extra']['url'], expected)

    def test_logger_exc_info(self):
        try:
            raise ValueError('This is a test ValueError')
        except ValueError:
            record = self.make_record('This is a test info with an exception', exc_info=sys.exc_info())
        else:
            self.fail('Should have raised an exception')

        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)

        self.assertEqual(event['message'], 'This is a test info with an exception')
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEqual(exc['type'], 'ValueError')
        self.assertEqual(exc['value'], 'This is a test ValueError')
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEqual(msg['message'], 'This is a test info with an exception')
        self.assertEqual(msg['params'], ())

    def test_message_params(self):
        record = self.make_record('This is a test of %s', args=('args',))
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEqual(event['message'], 'This is a test of args')
        msg = event['sentry.interfaces.Message']
        self.assertEqual(msg['message'], 'This is a test of %s')
        expected = ("'args'",) if six.PY3 else ("u'args'",)
        self.assertEqual(msg['params'], expected)

    def test_record_stack(self):
        record = self.make_record('This is a test of stacks', extra={'stack': True})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        frames = event['sentry.interfaces.Stacktrace']['frames']
        self.assertNotEquals(len(frames), 1)
        frame = frames[0]
        self.assertEqual(frame['module'], 'raven.handlers.logging')
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        self.assertEqual(event['culprit'], 'root in make_record')
        self.assertEqual(event['message'], 'This is a test of stacks')

    def test_no_record_stack(self):
        record = self.make_record('This is a test with no stacks', extra={'stack': False})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEqual(event['message'], 'This is a test with no stacks')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)

    def test_explicit_stack(self):
        record = self.make_record('This is a test of stacks', extra={'stack': iter_stack_frames()})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        assert 'sentry.interfaces.Stacktrace' in event
        assert 'culprit' in event
        assert event['culprit'] == 'root in make_record'
        self.assertTrue('message' in event, event)
        self.assertEqual(event['message'], 'This is a test of stacks')
        self.assertFalse('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Message' in event)
        msg = event['sentry.interfaces.Message']
        self.assertEqual(msg['message'], 'This is a test of stacks')
        self.assertEqual(msg['params'], ())

    def test_extra_culprit(self):
        record = self.make_record('This is a test of stacks', extra={'culprit': 'foo in bar'})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEqual(event['culprit'], 'foo in bar')

    def test_extra_data_as_string(self):
        record = self.make_record('Message', extra={'data': 'foo'})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        expected = "'foo'" if six.PY3 else "u'foo'"
        self.assertEqual(event['extra']['data'], expected)

    def test_tags(self):
        record = self.make_record('Message', extra={'tags': {'foo': 'bar'}})
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        assert event['tags'] == {'foo': 'bar'}

    def test_tags_on_error(self):
        try:
            raise ValueError('This is a test ValueError')
        except ValueError:
            record = self.make_record('Message', extra={'tags': {'foo': 'bar'}}, exc_info=sys.exc_info())
        self.handler.emit(record)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)
        assert event['tags'] == {'foo': 'bar'}


class LoggingHandlerTest(TestCase):
    def test_client_arg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)
        self.assertEqual(handler.client, client)

    def test_client_kwarg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client=client)
        self.assertEqual(handler.client, client)

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
        self.assertEqual(handler.level, logging.NOTSET)
