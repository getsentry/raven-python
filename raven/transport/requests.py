"""
raven.transport.requests
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.conf import defaults
from raven.transport.http import HTTPTransport

try:
    import requests
    has_requests = True
except ImportError:
    has_requests = False


class RequestsHTTPTransport(HTTPTransport):

    scheme = ['requests+http', 'requests+https']

    def __init__(self, parsed_url, timeout=defaults.TIMEOUT, verify_ssl=True,
                 ca_certs=defaults.CA_BUNDLE):
        if not has_requests:
            raise ImportError('RequestsHTTPTransport requires requests.')

        super(RequestsHTTPTransport, self).__init__(parsed_url,
                                                    timeout=timeout,
                                                    verify_ssl=verify_ssl,
                                                    ca_certs=ca_certs)

        # remove the requests+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def send(self, data, headers):
        if self.verify_ssl:
            # If SSL verification is enabled use the provided CA bundle to
            # perform the verification.
            self.verify_ssl = self.ca_certs
        requests.post(self._url, data=data, headers=headers,
                      verify=self.verify_ssl, timeout=self.timeout)
