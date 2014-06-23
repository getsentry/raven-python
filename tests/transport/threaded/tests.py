import mock
import time
from raven.utils.testutils import TestCase

from raven.base import Client
from raven.transport.threaded import ThreadedHTTPTransport
from raven.utils.urlparse import urlparse


class DummyThreadedScheme(ThreadedHTTPTransport):
    def __init__(self, *args, **kwargs):
        super(ThreadedHTTPTransport, self).__init__(*args, **kwargs)
        self.events = []
        self.send_delay = 0

    def send_sync(self, data, headers, success_cb, failure_cb):
        # delay sending the message, to allow us to test that the shutdown
        # hook waits correctly
        time.sleep(self.send_delay)

        self.events.append((data, headers, success_cb, failure_cb))


class ThreadedTransportTest(TestCase):
    def setUp(self):
        self.url = "threaded+http://some_username:some_password@localhost:8143/1"
        self.client = Client(dsn=self.url)

    @mock.patch('raven.transport.http.HTTPTransport.send')
    def test_does_send(self, send):
        self.client.captureMessage(message='foo')

        time.sleep(0.1)

        # TODO: This test could be more precise by ensuring it's sending the same params that are sent
        # to the ThreadedHTTPTransport.send() method
        self.assertEqual(send.call_count, 1)

    def test_shutdown_waits_for_send(self):
        url = urlparse(self.url)
        transport = DummyThreadedScheme(url)
        transport.send_delay = 0.5

        data = self.client.build_msg('raven.events.Message', message='foo')
        transport.async_send(data, None, None, None)

        time.sleep(0.1)

        # this should wait for the message to get sent
        transport.get_worker().main_thread_terminated()

        self.assertEqual(len(transport.events), 1)
