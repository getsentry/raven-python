"""
raven.contrib.async
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from Queue import Queue
from raven.base import Client
from threading import Thread, Lock
import atexit
import os

SENTRY_WAIT_SECONDS = 10


class AsyncWorker(object):
    _terminator = object()

    def __init__(self):
        self._queue = Queue(-1)
        self._lock = Lock()
        self._thread = None
        self.start()

    def main_thread_terminated(self):
        size = self._queue.qsize()
        if size:
            print "Sentry attempts to send %s error messages" % size
            print "Waiting up to %s seconds" % SENTRY_WAIT_SECONDS
            if os.name == 'nt':
                print "Press Ctrl-Break to quit"
            else:
                print "Press Ctrl-C to quit"
            self.stop(timeout=SENTRY_WAIT_SECONDS)

    def start(self):
        """
        Starts the task thread.
        """
        self._lock.acquire()
        try:
            if not self._thread:
                self._thread = Thread(target=self._target)
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

    def queue(self, callback, kwargs):
        self._queue.put_nowait((callback, kwargs))

    def _target(self):
        while 1:
            record = self._queue.get()
            if record is self._terminator:
                break
            callback, kwargs = record
            callback(**kwargs)


class AsyncClient(Client):
    """
    This client uses a single background thread to dispatch errors.
    """
    def __init__(self, worker=None, *args, **kwargs):
        self.worker = worker or AsyncWorker()
        super(AsyncClient, self).__init__(*args, **kwargs)

    def send_sync(self, **kwargs):
        super(AsyncClient, self).send(**kwargs)

    def send(self, **kwargs):
        self.worker.queue(self.send_sync, kwargs)


class SentryWorker(object):
    """
    A WSGI middleware which provides ``environ['raven.worker']``
    that can be used by clients to process asynchronous tasks.

    >>> from raven.base import Client
    >>> application = SentryWorker(application)
    """
    def __init__(self, application):
        self.application = application
        self.worker = AsyncWorker()

    def __call__(self, environ, start_response):
        environ['raven.worker'] = self.worker
        for event in self.application(environ, start_response):
            yield event
