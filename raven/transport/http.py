"""
raven.transport.http
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.conf import defaults
from raven.transport.base import Transport
from raven.utils import six
from raven.utils.http import urlopen
from raven.utils.compat import urllib2


class HTTPTransport(Transport):

    scheme = ['sync+http', 'sync+https']

    def __init__(self, parsed_url, timeout=defaults.TIMEOUT, verify_ssl=False,
                 ca_certs=defaults.CA_BUNDLE):
        self.check_scheme(parsed_url)

        self._parsed_url = parsed_url
        self._url = parsed_url.geturl().split('+', 1)[-1]

        if isinstance(timeout, six.string_types):
            timeout = int(timeout)
        if isinstance(verify_ssl, six.string_types):
            verify_ssl = bool(int(verify_ssl))

        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.ca_certs = ca_certs

    def send(self, data, headers):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = urllib2.Request(self._url, headers=headers)

        response = urlopen(
            url=req,
            data=data,
            timeout=self.timeout,
            verify_ssl=self.verify_ssl,
            ca_certs=self.ca_certs,
        ).read()
        return response
