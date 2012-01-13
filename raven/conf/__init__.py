"""
raven.conf
~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import urlparse


def load(dsn, scope):
    """
    Parses a Sentry compatible DSN and loads it
    into the given scope.

    >>> import raven
    >>> dsn = 'https://public_key:secret_key@sentry.local/project_id'
    >>> raven.load(dsn, locals())
    """
    url = urlparse.urlparse(dsn)
    if url.scheme not in ('http', 'https'):
        raise ValueError('Unsupported Sentry DSN scheme: %r' % url.scheme)
    netloc = url.hostname
    if url.port and url.port != 80:
        netloc += ':%s' % url.port
    scope.update({
        'SENTRY_SERVERS': ['%s://%s/api/store/' % (url.scheme, netloc)],
        'SENTRY_PROJECT': url.path[1:],
        'SENTRY_PUBLIC_KEY': url.username,
        'SENTRY_SECRET_KEY': url.password,
    })
