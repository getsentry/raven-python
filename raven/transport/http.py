"""
raven.transport.http
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import sys

from raven.conf import defaults
from raven.transport.base import Transport
from raven.utils import six
from raven.utils.compat import urlopen, Request


class HTTPTransport(Transport):

    scheme = ['sync+http', 'sync+https']

    def __init__(self, parsed_url, timeout=defaults.TIMEOUT):
        self.check_scheme(parsed_url)

        self._parsed_url = parsed_url
        self._url = parsed_url.geturl().split('+', 1)[-1]

        if isinstance(timeout, six.string_types):
            timeout = int(timeout)
        self.timeout = timeout

    def send(self, data, headers):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = Request(self._url, headers=headers)

        if sys.version_info < (2, 6):
            response = urlopen(req, data).read()
        else:
            response = urlopen(req, data, self.timeout).read()
        return response
