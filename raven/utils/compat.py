"""
raven.utils.compat
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import


try:
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import HTTPError  # NOQA


try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen  # NOQA


try:
    from urllib import quote as urllib_quote
except ImportError:
    from urllib.parse import quote as urllib_quote  # NOQA


try:
    from queue import Queue
except ImportError:
    from Queue import Queue  # NOQA


try:
    import urlparse as _urlparse
except ImportError:
    from urllib import parse as _urlparse  # NOQA


try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # NOQA
