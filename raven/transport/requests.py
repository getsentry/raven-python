"""
raven.transport.requests
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.http import HTTPTransport

try:
    import requests
    has_requests = True
except:
    has_requests = False


class RequestsHTTPTransport(HTTPTransport):

    scheme = ['requests+http', 'requests+https']

    def __init__(self, parsed_url):
        if not has_requests:
            raise ImportError('RequestsHTTPTransport requires requests.')

        super(RequestsHTTPTransport, self).__init__(parsed_url)

        # remove the requests+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def send(self, data, headers):
        requests.post(self._url, data=data, headers=headers)
