"""
raven.transport.eventlet
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import sys

from raven.transport.http import HTTPTransport

try:
    import eventlet
    try:
        from eventlet.green import urllib2 as eventlet_urllib2
    except ImportError:
        from eventlet.green.urllib import request as eventlet_urllib2
    has_eventlet = True
except:
    has_eventlet = False


class EventletHTTPTransport(HTTPTransport):

    scheme = ['eventlet+http', 'eventlet+https']

    def __init__(self, parsed_url, pool_size=100, **kwargs):
        if not has_eventlet:
            raise ImportError('EventletHTTPTransport requires eventlet.')
        super(EventletHTTPTransport, self).__init__(parsed_url, **kwargs)
        # remove the eventlet+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def _send_payload(self, payload):
        req = eventlet_urllib2.Request(self._url, headers=payload[1])
        try:
            if sys.version_info < (2, 6):
                response = eventlet_urllib2.urlopen(req, payload[0]).read()
            else:
                response = eventlet_urllib2.urlopen(req, payload[0],
                                                    self.timeout).read()
            return response
        except Exception as err:
            return err

    def send(self, data, headers):
        """
        Spawn an async request to a remote webserver.
        """
        eventlet.spawn(self._send_payload, (data, headers))
