from __future__ import absolute_import

import mock
import time
import socket
import gevent.monkey

from raven.utils.testutils import TestCase
from raven.base import Client
from raven.transport.gevent import GeventedHTTPTransport


class GeventTransportTest(TestCase):
    def setUp(self):
        gevent.monkey.patch_socket()
        self.addCleanup(reload, socket)
        gevent.monkey.patch_time()
        self.addCleanup(reload, time)
        self.client = Client(
            dsn="gevent+http://some_username:some_password@localhost:8143/1",
        )

    @mock.patch.object(GeventedHTTPTransport, '_done')
    @mock.patch('raven.transport.http.HTTPTransport.send')
    def test_does_send(self, send, done):
        self.client.captureMessage(message='foo')
        time.sleep(0)
        self.assertEqual(send.call_count, 1)
        time.sleep(0)
        self.assertEquals(done.call_count, 1)
