"""
raven.contrib.async
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import warnings

from raven.base import Client
from raven.transport.threaded import AsyncWorker


class AsyncClient(Client):
    """
    This client uses a single background thread to dispatch errors.
    """
    def __init__(self, worker=None, *args, **kwargs):
        warnings.warn('AsyncClient is deprecated. Use the threaded+http transport instead.', DeprecationWarning)
        self.worker = worker or AsyncWorker()
        super(AsyncClient, self).__init__(*args, **kwargs)

    def send_sync(self, **kwargs):
        super(AsyncClient, self).send(**kwargs)

    def send(self, **kwargs):
        self.worker.queue(self.send_sync, kwargs)
