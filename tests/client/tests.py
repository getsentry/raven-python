# -*- coding: utf-8 -*-

import inspect
from socket import socket, AF_INET, SOCK_DGRAM
from unittest2 import TestCase
from raven.base import Client
from raven.utils.stacks import iter_stack_frames


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)


class ClientTest(TestCase):
    def setUp(self):
        self.client = TempStoreClient()

    def test_exception(self):
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
        self.assertEquals(frame['abs_path'], __file__)
        self.assertEquals(frame['filename'], 'tests/client/tests.py')
        self.assertEquals(frame['module'], __name__)
        self.assertEquals(frame['function'], 'test_exception')
        self.assertTrue('timestamp' in event)

    def test_message(self):
        self.client.create_from_text('test')

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
