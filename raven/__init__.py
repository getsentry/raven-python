"""
sentry
~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

__all__ = ('VERSION', 'Client', 'load')

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('raven').version
except Exception, e:
    VERSION = 'unknown'

from base import Client
from conf import load
