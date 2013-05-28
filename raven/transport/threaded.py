"""
raven.transport.threaded
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import atexit
import logging
import os
import time
import threading

from raven.utils import memoize
from raven.utils.compat import Queue, Full
from raven.transport.base import HTTPTransport, AsyncTransport

DEFAULT_TIMEOUT = 10
QUEUE_SIZE = 100

logger = logging.getLogger('sentry.errors')


class AsyncWorker(object):
    _terminator = object()

    def __init__(self, shutdown_timeout=DEFAULT_TIMEOUT, queue_size=QUEUE_SIZE):
        self._queue = Queue(queue_size)
        self._lock = threading.Lock()
        self._thread = None
        self.options = {
            'shutdown_timeout': shutdown_timeout,
        }
        self.start()

    def main_thread_terminated(self):
        size = self._queue.qsize()
        if not size:
            return

        timeout = self.options['shutdown_timeout']
        print("Sentry is attempting to send %s pending error messages" % size)
        print("Waiting up to %s seconds" % timeout)
        if os.name == 'nt':
            print("Press Ctrl-Break to quit")
        else:
            print("Press Ctrl-C to quit")
        self.stop(timeout=timeout)

    def start(self):
        """
        Starts the task thread.
        """
        if not self._thread:
            return

        self._lock.acquire()
        try:
            self._thread = threading.Thread(target=self._target)
            self._thread.setDaemon(True)
            self._thread.start()
        finally:
            self._lock.release()
            atexit.register(self.main_thread_terminated)

    def stop(self, timeout=None):
        """
        Stops the task thread. Synchronous!
        """
        if not self._thread:
            return

        self._lock.acquire()
        try:
            self._queue.put_nowait(self._terminator)
            self._thread.join(timeout=timeout)
            self._thread = None
        finally:
            self._lock.release()

    def queue(self, callback, *args, **kwargs):
        try:
            self._queue.put_nowait((callback, args, kwargs))
        except Full:
            logger.error('Unable to queue job (full)', exc_info=True)

    def _target(self):
        while 1:
            record = self._queue.get()
            if record is self._terminator:
                break
            callback, args, kwargs = record
            try:
                callback(*args, **kwargs)
            except Exception:
                logger.error('Failed processing job', exc_info=True)

            time.sleep(0)


class ThreadedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['threaded+http', 'threaded+https']

    def __init__(self, parsed_url, queue_size=QUEUE_SIZE):
        super(ThreadedHTTPTransport, self).__init__(parsed_url)

        # remove the threaded+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]
        self._queue_size = queue_size

    @memoize
    def worker(self):
        return AsyncWorker(queue_size=self._queue_size)

    def send_sync(self, data, headers, success_cb, failure_cb):
        try:
            super(ThreadedHTTPTransport, self).send(data, headers)
        except Exception as e:
            failure_cb(e)
        else:
            success_cb()

    def async_send(self, data, headers, success_cb, failure_cb):
        self.worker.queue(
            self.send_sync, data, headers, success_cb, failure_cb)
