import sys
# XXX: zeropc does not work under Python < 2.6 or pypy
if (sys.version_info < (2, 6, 0) or '__pypy__' in sys.builtin_module_names):
    from nose.plugins.skip import SkipTest
    raise SkipTest

import gevent
import os
import random
import shutil
import tempfile
import unittest2
import zerorpc

from raven.base import Client
from raven.contrib.zerorpc import SentryMiddleware


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

        self._server = zerorpc.Server(random)
        self._server.bind(self._server_endpoint)
        gevent.spawn(self._server.run)

        self._client = zerorpc.Client()
        self._client.connect(self._server_endpoint)

    def test_zerorpc_middleware(self):
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

    def tearDown(self):
        self._client.close()
        self._server.close()
        shutil.rmtree(self._socket_dir, ignore_errors=True)
