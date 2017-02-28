"""
raven.transport.http
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven._compat import string_types
from raven.conf import defaults
from raven.exceptions import APIError, RateLimited
from raven.transport.base import Transport
from raven.utils.http import urlopen
from raven.utils.compat import urllib2


class HTTPTransport(Transport):
    scheme = ['sync+http', 'sync+https']

    def __init__(self, parsed_url, timeout=defaults.TIMEOUT, verify_ssl=True,
                 ca_certs=defaults.CA_BUNDLE):
        self._parsed_url = parsed_url
        self._url = parsed_url.geturl().rsplit('+', 1)[-1]

        if isinstance(timeout, string_types):
            timeout = int(timeout)
        if isinstance(verify_ssl, string_types):
            verify_ssl = bool(int(verify_ssl))

        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.ca_certs = ca_certs

    def send(self, data, headers):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = urllib2.Request(self._url, headers=headers)

        try:
            response = urlopen(
                url=req,
                data=data,
                timeout=self.timeout,
                verify_ssl=self.verify_ssl,
                ca_certs=self.ca_certs,
            )
        except urllib2.HTTPError as exc:
            msg = exc.headers.get('x-sentry-error')
            code = exc.getcode()
            if code == 429:
                try:
                    retry_after = int(exc.headers.get('retry-after'))
                except (ValueError, TypeError):
                    retry_after = 0
                raise RateLimited(msg, retry_after)
            elif msg:
                raise APIError(msg, code)
            else:
                raise
        return response
