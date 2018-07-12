"""
raven.transport.threaded_requests
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport import RequestsHTTPTransport
from raven.transport.threaded import ThreadedTransport


class ThreadedRequestsHTTPTransport(RequestsHTTPTransport, ThreadedTransport):
    scheme = ['threaded+requests+http', 'threaded+requests+https']
