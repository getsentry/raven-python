# -*- coding: utf-8 -*-

import inspect
import mock
import raven
import time
from socket import socket, AF_INET, SOCK_DGRAM
from unittest2 import TestCase
from raven.base import Client, ClientState
from raven.utils.stacks import iter_stack_frames


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

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


class ClientTest(TestCase):
    def setUp(self):
        self.client = TempStoreClient()

    @mock.patch('raven.base.Client._send_remote')
    @mock.patch('raven.base.ClientState.should_try')
    def test_send_remote_failover(self, should_try, send_remote):
        should_try.return_value = True

        client = Client(
            servers=['http://example.com'],
            public_key='public',
            secret_key='secret',
            project=1,
        )

        # test error
        send_remote.side_effect = Exception()
        client.send_remote('http://example.com/api/store', 'foo')
        self.assertEquals(client.state.status, client.state.ERROR)

        # test recovery
        send_remote.side_effect = None
        client.send_remote('http://example.com/api/store', 'foo')
        self.assertEquals(client.state.status, client.state.ONLINE)

    @mock.patch('raven.base.Client.send_remote')
    @mock.patch('raven.base.get_signature')
    @mock.patch('raven.base.time.time')
    def test_send(self, time, get_signature, send_remote):
        time.return_value = 1328055286.51
        get_signature.return_value = 'signature'
        client = Client(
            servers=['http://example.com'],
            public_key='public',
            secret_key='secret',
            project=1,
        )
        client.send(**{
            'foo': 'bar',
        })
        send_remote.assert_called_once_with(
            url='http://example.com',
            data='eJyrVkrLz1eyUlBKSixSqgUAIJgEVA==',
            headers={
                'Content-Type': 'application/octet-stream',
                'X-Sentry-Auth': 'Sentry sentry_timestamp=1328055286.51, sentry_signature=signature, '
                'sentry_client=raven-python/%s, sentry_version=2.0, sentry_key=public' % (raven.VERSION,)
            },
        )

    def test_encode_decode(self):
        data = {'foo': 'bar'}
        encoded = self.client.encode(data)
        self.assertTrue(type(encoded), str)
        self.assertEquals(data, self.client.decode(encoded))

    def test_dsn(self):
        client = Client(dsn='http://public:secret@example.com/1')
        self.assertEquals(client.servers, ['http://example.com/api/store/'])
        self.assertEquals(client.project, '1')
        self.assertEquals(client.public_key, 'public')
        self.assertEquals(client.secret_key, 'secret')

    def test_dsn_as_first_arg(self):
        client = Client('http://public:secret@example.com/1')
        self.assertEquals(client.servers, ['http://example.com/api/store/'])
        self.assertEquals(client.project, '1')
        self.assertEquals(client.public_key, 'public')
        self.assertEquals(client.secret_key, 'secret')

    def test_slug_in_dsn(self):
        client = Client('http://public:secret@example.com/slug-name')
        self.assertEquals(client.servers, ['http://example.com/api/store/'])
        self.assertEquals(client.project, 'slug-name')
        self.assertEquals(client.public_key, 'public')
        self.assertEquals(client.secret_key, 'secret')

    def test_invalid_servers_with_dsn(self):
        self.assertRaises(ValueError, Client, 'foo', dsn='http://public:secret@example.com/1')

    def test_explicit_message_on_message_event(self):
        self.client.capture('Message', message='test', data={
            'message': 'foo'
        })

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'foo')

    def test_explicit_message_on_exception_event(self):
        try:
            raise ValueError('foo')
        except:
            self.client.capture('Exception', data={'message': 'foobar'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'foobar')

    def test_exception_event(self):
        try:
            raise ValueError('foo')
        except:
            self.client.capture('Exception')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'ValueError: foo')
        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'foo')
        self.assertEquals(exc['module'], ValueError.__module__)  # this differs in some Python versions
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        frames = event['sentry.interfaces.Stacktrace']
        self.assertEquals(len(frames['frames']), 1)
        frame = frames['frames'][0]
        self.assertEquals(frame['abs_path'], __file__.replace('.pyc', '.py'))
        self.assertEquals(frame['filename'], 'tests/client/tests.py')
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['function'], 'test_exception_event')
        self.assertTrue('timestamp' in event)

    def test_message_event(self):
        self.client.capture('Message', message='test')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        self.assertFalse('sentry.interfaces.Stacktrace' in event)
        self.assertTrue('timestamp' in event)

    def test_stack_explicit_frames(self):
        def bar():
            return inspect.stack()

        frames = bar()

        self.client.create_from_text('test', stack=iter_stack_frames(frames))

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        self.assertEquals(len(frames), len(event['sentry.interfaces.Stacktrace']['frames']))
        for frame, frame_i in zip(frames, event['sentry.interfaces.Stacktrace']['frames']):
            self.assertEquals(frame[0].f_code.co_filename, frame_i['abs_path'])
            self.assertEquals(frame[0].f_code.co_name, frame_i['function'])

    def test_stack_auto_frames(self):
        self.client.create_from_text('test', stack=True)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['message'], 'test')
        self.assertTrue('sentry.interfaces.Stacktrace' in event)
        self.assertTrue('timestamp' in event)

    def test_site(self):
        self.client.capture('Message', message='test', data={'site': 'test'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['site'], 'test')
        self.assertTrue('timestamp' in event)

    def test_implicit_site(self):
        self.client = TempStoreClient(site='foo')
        self.client.capture('Message', message='test')

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['site'], 'foo')

    def test_logger(self):
        self.client.capture('Message', message='test', data={'logger': 'test'})

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)
        self.assertEquals(event['logger'], 'test')
        self.assertTrue('timestamp' in event)


class ClientUDPTest(TestCase):
    def setUp(self):
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_socket.bind(('127.0.0.1', 0))
        self.client = Client(servers=["udp://%s:%s" % self.server_socket.getsockname()], key='BassOmatic')

    def test_delivery(self):
        self.client.create_from_text('test')
        data, address = self.server_socket.recvfrom(2**16)
        self.assertTrue("\n\n" in data)
        header, payload = data.split("\n\n")
        for substring in ("sentry_timestamp=", "sentry_client=", "sentry_signature="):
            self.assertTrue(substring in header)

    def tearDown(self):
        self.server_socket.close()
