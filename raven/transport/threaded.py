"""
raven.transport.threaded
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import atexit
import logging
import time
import threading
import os

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.utils.compat import Queue

DEFAULT_TIMEOUT = 10

logger = logging.getLogger('sentry.errors')


class AsyncWorker(object):
    _terminator = object()

    def __init__(self, shutdown_timeout=DEFAULT_TIMEOUT):
        self._queue = Queue(-1)
        self._lock = threading.Lock()
        self._thread = None
        self.options = {
            'shutdown_timeout': shutdown_timeout,
        }
        self.start()

    def main_thread_terminated(self):
        size = self._queue.qsize()
        if size:
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
        self._lock.acquire()
        try:
            if not self._thread:
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
        self._lock.acquire()
        try:
            if self._thread:
                self._queue.put_nowait(self._terminator)
                self._thread.join(timeout=timeout)
                self._thread = None
        finally:
            self._lock.release()

    def queue(self, callback, *args, **kwargs):
        self._queue.put_nowait((callback, args, kwargs))

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

    scheme = ['http', 'https', 'threaded+http', 'threaded+https']

    def get_worker(self):
        if not hasattr(self, '_worker'):
            self._worker = AsyncWorker()
        return self._worker

    def send_sync(self, data, headers, success_cb, failure_cb):
        try:
            super(ThreadedHTTPTransport, self).send(data, headers)
        except Exception as e:
            failure_cb(e)
        else:
            success_cb()

    def async_send(self, data, headers, success_cb, failure_cb):
        self.get_worker().queue(
            self.send_sync, data, headers, success_cb, failure_cb)
