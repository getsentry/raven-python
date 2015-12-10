import mock
import os
import time
from tempfile import mkstemp

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


class LoggingThreadedScheme(ThreadedHTTPTransport):
    def __init__(self, filename, *args, **kwargs):
        super(LoggingThreadedScheme, self).__init__(*args, **kwargs)
        self.filename = filename

    def send_sync(self, data, headers, success_cb, failure_cb):
        with open(self.filename, 'a') as log:
            log.write("{0} {1}\n".format(os.getpid(), data['message']))


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

    def test_fork_spawns_anew(self):
        url = urlparse(self.url)
        transport = DummyThreadedScheme(url)
        transport.send_delay = 0.5

        data = self.client.build_msg('raven.events.Message', message='foo')

        pid = os.fork()
        if pid == 0:
            time.sleep(0.1)

            transport.async_send(data, None, None, None)

            # this should wait for the message to get sent
            transport.get_worker().main_thread_terminated()

            self.assertEqual(len(transport.events), 1)
            # Use os._exit here so that py.test gets not confused about
            # what the hell we're doing here.
            os._exit(0)
        else:
            os.waitpid(pid, 0)

    def test_fork_with_active_worker(self):
        # Test threaded transport when forking with an active worker.
        # Forking a process doesn't clone the worker thread - make sure
        # logging from both processes still works.
        event1 = self.client.build_msg('raven.events.Message', message='parent')
        event2 = self.client.build_msg('raven.events.Message', message='child')
        url = urlparse(self.url)
        fd, filename = mkstemp()
        try:
            os.close(fd)
            transport = LoggingThreadedScheme(filename, url)

            # Log from the parent process - starts the worker thread
            transport.async_send(event1, None, None, None)
            childpid = os.fork()

            if childpid == 0:
                # Log from the child process
                transport.async_send(event2, None, None, None)

                # Ensure threaded worker has finished
                transport.get_worker().stop()
                os._exit(0)

            # Wait for the child process to finish
            os.waitpid(childpid, 0)
            assert os.path.isfile(filename)

            # Ensure threaded worker has finished
            transport.get_worker().stop()

            with open(filename, 'r') as logfile:
                events = dict(x.strip().split() for x in logfile.readlines())

            # Check parent and child both logged successfully
            assert events == {
                str(os.getpid()): 'parent',
                str(childpid): 'child',
            }
        finally:
            os.remove(filename)
