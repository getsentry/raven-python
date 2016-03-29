# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
import mock
import raven
import time
import six
import os

from raven.base import Client, ClientState
from raven.exceptions import RateLimited
from raven.transport import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.utils.stacks import iter_stack_frames
from raven.utils.testutils import TestCase


class TempStoreClient(Client):
    def __init__(self, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(**kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class ClientStateTest(TestCase):
    def test_should_try_online(self):
        state = ClientState()
        self.assertEquals(state.should_try(), True)

    def test_should_try_new_error(self):
        state = ClientState()
        state.status = state.ERROR
        state.last_check = time.time()
        state.retry_number = 1
        self.assertEquals(state.should_try(), False)

    def test_should_try_time_passed_error(self):
        state = ClientState()
        state.status = state.ERROR
        state.last_check = time.time() - 10
        state.retry_number = 1
        self.assertEquals(state.should_try(), True)

    def test_set_fail(self):
        state = ClientState()
        state.set_fail()
        self.assertEquals(state.status, state.ERROR)
        self.assertNotEquals(state.last_check, None)
        self.assertEquals(state.retry_number, 1)

    def test_set_success(self):
        state = ClientState()
        state.status = state.ERROR
        state.last_check = 'foo'
        state.retry_number = 0
        state.set_success()
        self.assertEquals(state.status, state.ONLINE)
        self.assertEquals(state.last_check, None)
        self.assertEquals(state.retry_number, 0)

    def test_should_try_retry_after(self):
        state = ClientState()
        state.status = state.ERROR
        state.last_check = time.time()
        state.retry_number = 1
        state.retry_after = 1
        self.assertFalse(state.should_try())

    def test_should_try_retry_after_passed(self):
        state = ClientState()
        state.status = state.ERROR
        state.last_check = time.time() - 1
        state.retry_number = 1
        state.retry_after = 1
        self.assertTrue(state.should_try())


class ClientTest(TestCase):
    def setUp(self):
        self.client = TempStoreClient()

    def test_first_client_is_singleton(self):
        from raven import base
        base.Raven = None

        client = Client()
        client2 = Client()

        assert base.Raven is client
        assert client is not client2

    def test_client_picks_up_env_dsn(self):
        DSN = 'sync+http://public:secret@example.com/1'
        PUBLIC_DSN = '//public@example.com/1'
        with mock.patch.dict(os.environ, {'SENTRY_DSN': DSN}):
            client = Client()
            assert client.remote.get_public_dsn() == PUBLIC_DSN
            client = Client('')
            assert client.remote.get_public_dsn() == PUBLIC_DSN

    @mock.patch('raven.transport.http.HTTPTransport.send')
    @mock.patch('raven.base.ClientState.should_try')
    def test_send_remote_failover(self, should_try, send):
        should_try.return_value = True

        client = Client(
            dsn='sync+http://public:secret@example.com/1'
        )

        # test error
        send.side_effect = Exception()
        client.send_remote('sync+http://example.com/api/store', client.encode({}))
        self.assertEquals(client.state.status, client.state.ERROR)

        # test recovery
        send.side_effect = None
        client.send_remote('sync+http://example.com/api/store', client.encode({}))
        self.assertEquals(client.state.status, client.state.ONLINE)

    @mock.patch('raven.transport.http.HTTPTransport.send')
    @mock.patch('raven.base.ClientState.should_try')
    def test_send_remote_failover_with_retry_after(self, should_try, send):
        should_try.return_value = True

        client = Client(
            dsn='sync+http://public:secret@example.com/1'
        )

        # test error
        send.side_effect = RateLimited('foo', 5)
        client.send_remote('sync+http://example.com/api/1/store/', client.encode({}))
        self.assertEquals(client.state.status, client.state.ERROR)
        self.assertEqual(client.state.retry_after, 5)

        # test recovery
        send.side_effect = None
        client.send_remote('sync+http://example.com/api/1/store/', client.encode({}))
        self.assertEquals(client.state.status, client.state.ONLINE)
        self.assertEqual(client.state.retry_after, 0)

    @mock.patch('raven.conf.remote.RemoteConfig.get_transport')
    @mock.patch('raven.base.ClientState.should_try')
    def test_async_send_remote_failover(self, should_try, get_transport):
        should_try.return_value = True
        async_transport = AsyncTransport()
        async_transport.async_send = async_send = mock.Mock()
        get_transport.return_value = async_transport

        client = Client(
            dsn='http://public:secret@example.com/1',
        )

        # test immediate raise of error
        async_send.side_effect = Exception()
        client.send_remote('http://example.com/api/1/store/', client.encode({}))
        self.assertEquals(client.state.status, client.state.ERROR)

        # test recovery
        client.send_remote('http://example.com/api/1/store/', client.encode({}))
        success_cb = async_send.call_args[0][2]
        success_cb()
        self.assertEquals(client.state.status, client.state.ONLINE)

        # test delayed raise of error
        client.send_remote('http://example.com/api/1/store/', client.encode({}))
        failure_cb = async_send.call_args[0][3]
        failure_cb(Exception())
        self.assertEquals(client.state.status, client.state.ERROR)

    @mock.patch('raven.base.Client.send_remote')
    @mock.patch('raven.base.time.time')
    def test_send(self, time, send_remote):
        time.return_value = 1328055286.51
        client = Client(
            dsn='http://public:secret@example.com/1',
        )
        client.send(**{
            'foo': 'bar',
        })
        send_remote.assert_called_once_with(
            url='http://example.com/api/1/store/',
            data=client.encode({'foo': 'bar'}),
            headers={
                'User-Agent': 'raven-python/%s' % (raven.VERSION,),
                'Content-Type': 'application/octet-stream',
                'Content-Encoding': client.get_content_encoding(),
                'X-Sentry-Auth': (
                    'Sentry sentry_timestamp=1328055286.51, '
                    'sentry_client=raven-python/%s, sentry_version=6, '
                    'sentry_key=public, '
                    'sentry_secret=secret' % (raven.VERSION,))
            },
        )

    @mock.patch('raven.base.Client.send_remote')
    @mock.patch('raven.base.time.time')
    def test_send_with_auth_header(self, time, send_remote):
        time.return_value = 1328055286.51
        client = Client(
            dsn='http://public:secret@example.com/1',
        )
        client.send(auth_header='foo', **{
            'foo': 'bar',
        })
        send_remote.assert_called_once_with(
            url='http://example.com/api/1/store/',
            data=client.encode({'foo': 'bar'}),
            headers={
                'User-Agent': 'raven-python/%s' % (raven.VERSION,),
                'Content-Type': 'application/octet-stream',
                'Content-Encoding': client.get_content_encoding(),
                'X-Sentry-Auth': 'foo',
            },
        )

    @mock.patch('raven.transport.http.HTTPTransport.send')
    @mock.patch('raven.base.ClientState.should_try')
    def test_raise_exception_on_send_error(self, should_try, _send_remote):
        should_try.return_value = True
        client = Client(
            dsn='sync+http://public:secret@example.com/1',
        )

        # Test for the default behaviour in which a send error is handled by the client
        _send_remote.side_effect = Exception()
        client.capture('Message', data={}, date=None, time_spent=10,
                       extra={}, stack=None, tags=None, message='Test message')
        assert client.state.status == client.state.ERROR

        # Test for the case in which a send error is raised to the calling frame.
        client = Client(
            dsn='sync+http://public:secret@example.com/1',
            raise_send_errors=True,
        )
        with self.assertRaises(Exception):
            client.capture('Message', data={}, date=None, time_spent=10,
                           extra={}, stack=None, tags=None, message='Test message')

    def test_encode_decode(self):
        data = {'foo': 'bar'}
        encoded = self.client.encode(data)
        self.assertTrue(type(encoded), str)
        self.assertEquals(data, self.client.decode(encoded))

    def test_get_public_dsn(self):
        client = Client('http://public:secret@example.com/1')
        public_dsn = client.get_public_dsn()
        self.assertEquals(public_dsn, '//public@example.com/1')

    def test_explicit_message_on_message_event(self):
        self.client.captureMessage(message='test', data={
            'message': 'foo'
        })

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'foo')

    def test_message_from_kwargs(self):
        try:
            raise ValueError('foo')
        except ValueError:
            self.client.captureException(message='test', data={})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')

    def test_explicit_message_on_exception_event(self):
        try:
            raise ValueError('foo')
        except ValueError:
            self.client.captureException(data={'message': 'foobar'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'foobar')

    def test_exception_event(self):
        try:
            raise ValueError('foo')
        except ValueError:
            self.client.captureException()

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'ValueError: foo')
        self.assertTrue('exception' in event)
        exc = event['exception']['values'][0]
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'foo')
        self.assertEquals(exc['module'], ValueError.__module__)  # this differs in some Python versions
        assert 'stacktrace' not in event
        stacktrace = exc['stacktrace']
        self.assertEquals(len(stacktrace['frames']), 1)
        frame = stacktrace['frames'][0]
        self.assertEquals(frame['abs_path'], __file__.replace('.pyc', '.py'))
        self.assertEquals(frame['filename'], 'tests/base/tests.py')
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['function'], 'test_exception_event')
        self.assertTrue('timestamp' in event)

    def test_exception_event_true_exc_info(self):
        try:
            raise ValueError('foo')
        except ValueError:
            self.client.captureException(exc_info=True)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'ValueError: foo')
        self.assertTrue('exception' in event)
        exc = event['exception']['values'][0]
        stacktrace = exc['stacktrace']
        self.assertEquals(len(stacktrace['frames']), 1)
        frame = stacktrace['frames'][0]
        self.assertEquals(frame['abs_path'], __file__.replace('.pyc', '.py'))
        self.assertEquals(frame['filename'], 'tests/base/tests.py')
        self.assertEquals(frame['module'], __name__)

    def test_decorator_preserves_function(self):
        @self.client.capture_exceptions
        def test1():
            return 'foo'

        self.assertEquals(test1(), 'foo')

    class DecoratorTestException(Exception):
        pass

    def test_decorator_functionality(self):
        @self.client.capture_exceptions
        def test2():
            raise self.DecoratorTestException()

        try:
            test2()
        except self.DecoratorTestException:
            pass

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'DecoratorTestException')
        exc = event['exception']['values'][0]
        self.assertEquals(exc['type'], 'DecoratorTestException')
        self.assertEquals(exc['module'], self.DecoratorTestException.__module__)
        stacktrace = exc['stacktrace']
        # this is a wrapped class object with __call__ so three frames are expected
        self.assertEquals(len(stacktrace['frames']), 3)
        frame = stacktrace['frames'][-1]
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['function'], 'test2')

    def test_decorator_filtering(self):
        @self.client.capture_exceptions(self.DecoratorTestException)
        def test3():
            raise Exception()

        try:
            test3()
        except Exception:
            pass

        self.assertEquals(len(self.client.events), 0)

    def test_context_manager_functionality(self):
        def test4():
            raise self.DecoratorTestException()

        try:
            with self.client.capture_exceptions():
                test4()
        except self.DecoratorTestException:
            pass

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'DecoratorTestException')
        exc = event['exception']['values'][0]
        self.assertEquals(exc['type'], 'DecoratorTestException')
        self.assertEquals(exc['module'], self.DecoratorTestException.__module__)
        stacktrace = exc['stacktrace']
        # three frames are expected: test4, `with` block and context manager internals
        self.assertEquals(len(stacktrace['frames']), 3)
        frame = stacktrace['frames'][-1]
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['function'], 'test4')

    def test_content_manager_filtering(self):
        def test5():
            raise Exception()

        try:
            with self.client.capture_exceptions(self.DecoratorTestException):
                test5()
        except Exception:
            pass

        self.assertEquals(len(self.client.events), 0)

    def test_message_event(self):
        self.client.captureMessage(message='test')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        assert 'stacktrace' not in event
        self.assertTrue('timestamp' in event)

    def test_fingerprint(self):
        self.client.captureMessage(
            message='test',
            fingerprint=['{{ default }}', 'foobar'],
        )

        assert len(self.client.events) == 1
        event = self.client.events.pop(0)
        assert event['fingerprint'] == ['{{ default }}', 'foobar']

    def test_context(self):
        self.client.context.merge({
            'tags': {'foo': 'bar'},
        })
        try:
            raise ValueError('foo')
        except ValueError:
            self.client.captureException()
        else:
            self.fail('Exception should have been raised')

        assert len(self.client.events) == 1
        event = self.client.events.pop(0)
        assert event['tags'] == {'foo': 'bar'}

    def test_stack_explicit_frames(self):
        def bar():
            return inspect.stack()

        frames = bar()

        self.client.captureMessage('test', stack=iter_stack_frames(frames))

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        assert 'stacktrace' in event
        self.assertEquals(len(frames), len(event['stacktrace']['frames']))
        for frame, frame_i in zip(frames, event['stacktrace']['frames']):
            self.assertEquals(frame[0].f_code.co_filename, frame_i['abs_path'])
            self.assertEquals(frame[0].f_code.co_name, frame_i['function'])

    def test_stack_auto_frames(self):
        self.client.captureMessage('test', stack=True)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        self.assertTrue('stacktrace' in event)
        self.assertTrue('timestamp' in event)

    def test_site(self):
        self.client.captureMessage(message='test', data={'site': 'test'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        assert 'site' in event['tags']
        assert event['tags']['site'] == 'test'

    def test_implicit_site(self):
        self.client = TempStoreClient(site='foo')
        self.client.captureMessage(message='test')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        assert 'site' in event['tags']
        assert event['tags']['site'] == 'foo'

    def test_logger(self):
        self.client.captureMessage(message='test', data={'logger': 'test'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['logger'], 'test')
        self.assertTrue('timestamp' in event)

    def test_tags(self):
        self.client.captureMessage(message='test', tags={'logger': 'test'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['tags'], {'logger': 'test'})

    def test_client_extra_context(self):
        self.client.extra = {
            'foo': 'bar',
            'logger': 'baz',
        }
        self.client.captureMessage(message='test', extra={'logger': 'test'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        if six.PY3:
            expected = {'logger': "'test'", 'foo': "'bar'"}
        else:
            expected = {'logger': "u'test'", 'foo': "u'bar'"}
        self.assertEquals(event['extra'], expected)

    def test_transport_registration(self):
        client = Client('http://public:secret@example.com/1',
                        transport=HTTPTransport)
        assert type(client.remote.get_transport()) is HTTPTransport

        client = Client('sync+http://public:secret@example.com/1')
        assert type(client.remote.get_transport()) is HTTPTransport

    def test_marks_in_app_frames_for_stacktrace(self):
        client = TempStoreClient(
            include_paths=['foo'],
            exclude_paths=['foo.bar'],
        )
        client.captureMessage('hello', data={
            'stacktrace': {
                'frames': [
                    {'module': 'foo'},
                    {'module': 'bar'},
                    {'module': 'foo.bar'},
                    {'module': 'foo.baz'},
                ]
            }
        })

        event = client.events.pop(0)
        frames = event['stacktrace']['frames']
        assert frames[0]['in_app']
        assert not frames[1]['in_app']
        assert not frames[2]['in_app']
        assert frames[3]['in_app']

    def test_marks_in_app_frames_for_exception(self):
        client = TempStoreClient(
            include_paths=['foo'],
            exclude_paths=['foo.bar'],
        )
        client.captureMessage('hello', data={
            'exception': {
                'values': [{
                    'stacktrace': {
                        'frames': [
                            {'module': 'foo'},
                            {'module': 'bar'},
                            {'module': 'foo.bar'},
                            {'module': 'foo.baz'},
                        ]
                    }
                }]
            }
        })

        event = client.events.pop(0)
        frames = event['exception']['values'][0]['stacktrace']['frames']
        assert frames[0]['in_app']
        assert not frames[1]['in_app']
        assert not frames[2]['in_app']
        assert frames[3]['in_app']
