import mock
import time
from unittest2 import TestCase

from raven.base import Client
from raven.transport.threaded import ThreadedHTTPTransport


class DummyThreadedScheme(ThreadedHTTPTransport):

    scheme = ['threaded+mock']

    def __init__(self, *args, **kwargs):
        super(ThreadedHTTPTransport, self).__init__(*args, **kwargs)
        self.events = []

    def send_sync(self, data, headers):
        self.events.append((data, headers))


class ThreadedTransportTest(TestCase):
    def setUp(self):
        self.client = Client(
            dsn="threaded+http://some_username:some_password@localhost:8143/1",
        )

    @mock.patch('raven.transport.base.HTTPTransport.send')
    def test_does_send(self, send):
        self.client.captureMessage(message='foo')

        time.sleep(0)

        # TODO: This test could be more precise by ensuring it's sending the same params that are sent
        # to the ThreadedHTTPTransport.send() method
        send.assert_called_once()
