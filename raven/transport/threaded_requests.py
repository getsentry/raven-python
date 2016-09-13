"""
raven.transport.threaded_requests
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.base import AsyncTransport
from raven.transport.requests import RequestsHTTPTransport
from raven.transport.threaded import AsyncWorker


class ThreadedRequestsHTTPTransport(AsyncTransport, RequestsHTTPTransport):

    scheme = ['threaded+requests+http', 'threaded+requests+https']

    def get_worker(self):
        if not hasattr(self, '_worker'):
            self._worker = AsyncWorker()
        return self._worker

    def send_sync(self, data, headers, success_cb, failure_cb):
        try:
            super(ThreadedRequestsHTTPTransport, self).send(data, headers)
        except Exception as e:
            failure_cb(e)
        else:
            success_cb()

    def async_send(self, data, headers, success_cb, failure_cb):
        self.get_worker().queue(
            self.send_sync, data, headers, success_cb, failure_cb)
