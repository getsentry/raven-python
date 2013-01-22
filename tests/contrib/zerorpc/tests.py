import os
import pytest
import random
import shutil
import tempfile
import unittest2

from raven.base import Client
from raven.contrib.zerorpc import SentryMiddleware

zerorpc = pytest.importorskip("zerorpc")
gevent = pytest.importorskip("gevent")


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class ZeroRPCTest(unittest2.TestCase):
    def setUp(self):
        self._socket_dir = tempfile.mkdtemp(prefix='ravenzerorpcunittest')
        self._server_endpoint = 'ipc://{0}'.format(os.path.join(
                    self._socket_dir, 'random_zeroserver'
        ))

        self._sentry = TempStoreClient()
        zerorpc.Context.get_instance().register_middleware(SentryMiddleware(
                    client=self._sentry
        ))

    def test_zerorpc_middleware_with_reqrep(self):
        self._server = zerorpc.Server(random)
        self._server.bind(self._server_endpoint)
        gevent.spawn(self._server.run)

        self._client = zerorpc.Client()
        self._client.connect(self._server_endpoint)

        try:
            self._client.choice([])
        except zerorpc.exceptions.RemoteError, ex:
            self.assertEqual(ex.name, 'IndexError')
            self.assertEqual(len(self._sentry.events), 1)
            exc = self._sentry.events[0]['sentry.interfaces.Exception']
            self.assertEqual(exc['type'], 'IndexError')
            frames = self._sentry.events[0]['sentry.interfaces.Stacktrace']['frames']
            self.assertEqual(frames[0]['function'], 'choice')
            self.assertEqual(frames[0]['module'], 'random')
            return

        self.fail('An IndexError exception should have been raised an catched')

    def test_zerorpc_middleware_with_pushpull(self):
        self._server = zerorpc.Puller(random)
        self._server.bind(self._server_endpoint)
        gevent.spawn(self._server.run)

        self._client = zerorpc.Pusher()
        self._client.connect(self._server_endpoint)

        self._client.choice([])

        for attempt in xrange(0, 10):
            gevent.sleep(0.1)
            if len(self._sentry.events):
                exc = self._sentry.events[0]['sentry.interfaces.Exception']
                self.assertEqual(exc['type'], 'IndexError')
                frames = self._sentry.events[0]['sentry.interfaces.Stacktrace']['frames']
                self.assertEqual(frames[0]['function'], 'choice')
                self.assertEqual(frames[0]['module'], 'random')
                return

        self.fail('An IndexError exception should have been sent to Sentry')

    def tearDown(self):
        self._client.close()
        self._server.close()
        shutil.rmtree(self._socket_dir, ignore_errors=True)
