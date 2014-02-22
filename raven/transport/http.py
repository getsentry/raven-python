"""
raven.transport.http
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import httplib
import socket
import ssl
import sys

from raven.conf import defaults
from raven.transport.base import Transport
from raven.utils import six
from raven.utils.compat import urllib2


def urlopen_py2(url, data=None, timeout=defaults.TIMEOUT, ca_certs=None,
                verify_ssl=False):

    class ValidHTTPSConnection(httplib.HTTPConnection):
        "This class allows communication via SSL."

        default_port = httplib.HTTPS_PORT

        def __init__(self, *args, **kwargs):
            httplib.HTTPConnection.__init__(self, *args, **kwargs)

        def connect(self):
            "Connect to a host on a given (SSL) port."

            sock = socket.create_connection(
                (self.host, self.port), self.timeout, self.source_address)
            if self._tunnel_host:
                self.sock = sock
                self._tunnel()
            self.sock = ssl.wrap_socket(
                sock, ca_certs=ca_certs, cert_reqs=ssl.CERT_REQUIRED)

    class ValidHTTPSHandler(urllib2.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(ValidHTTPSConnection, req)

    if verify_ssl:
        handlers = [ValidHTTPSHandler]
    else:
        handlers = []

    opener = urllib2.build_opener(*handlers)

    if sys.version_info < (2, 6):
        default_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            return opener.open(url, data)
        finally:
            socket.setdefaulttimeout(default_timeout)
    return opener.open(url, data, timeout)


def urlopen(url, data=None, timeout=defaults.TIMEOUT, ca_certs=None,
            verify_ssl=False):
    if not six.PY3:
        return urlopen_py2(url, data, timeout, ca_certs, verify_ssl)

    return urllib2.urlopen(
        url, data, timeout,
        cafile=ca_certs,
        cadefault=verify_ssl,
    )


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
