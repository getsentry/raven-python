"""
raven.transport.gevent
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport

from raven.utils.http import urlopen
from raven.utils.compat import urllib2

try:
    import gevent
    # gevent 1.0bN renamed coros to lock
    try:
        from gevent.lock import Semaphore
    except ImportError:
        from gevent.coros import Semaphore  # NOQA
    has_gevent = True
except:
    has_gevent = None


class GeventedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['gevent+http', 'gevent+https']

    def __init__(self, parsed_url, maximum_outstanding_requests=100,
                 oneway=False):
        if not has_gevent:
            raise ImportError('GeventedHTTPTransport requires gevent.')
        self._lock = Semaphore(maximum_outstanding_requests)
        self._oneway = oneway == 'true'

        super(GeventedHTTPTransport, self).__init__(parsed_url)

        # remove the gevent+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def async_send(self, data, headers, success_cb, failure_cb):
        """
        Spawn an async request to a remote webserver.
        """
        if not self._oneway:
            self._lock.acquire()
            return gevent.spawn(
                super(GeventedHTTPTransport, self).send, data, headers
            ).link(lambda x: self._done(x, success_cb, failure_cb))
        else:
            req = urllib2.Request(self._url, headers=headers)
            return urlopen(url=req,
                           data=data,
                           timeout=self.timeout,
                           verify_ssl=self.verify_ssl,
                           ca_certs=self.ca_certs)

    def _done(self, greenlet, success_cb, failure_cb, *args):
        self._lock.release()
        if greenlet.successful():
            success_cb()
        else:
            failure_cb(greenlet.exception)
