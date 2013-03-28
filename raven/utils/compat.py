"""
raven.utils.compat
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

try:
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import HTTPError


try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen


try:
    from urllib import quote as urllib_quote
except ImportError:
    from urllib.parse import quote as urllib_quote


try:
    from queue import Queue
except ImportError:
    from Queue import Queue


try:
    import urlparse as _urlparse
except ImportError:
    from urllib import parse as _urlparse


try:
    from unittest import TestCase, skipIf
except ImportError:
    from unittest2 import TestCase, skipIf

