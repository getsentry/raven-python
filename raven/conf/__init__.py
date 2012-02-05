"""
raven.conf
~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging
import urlparse


def load(dsn, scope=None):
    """
    Parses a Sentry compatible DSN and loads it
    into the given scope.

    >>> import raven

    >>> dsn = 'https://public_key:secret_key@sentry.local/project_id'

    >>> # Apply configuratio to local scope
    >>> raven.load(dsn, locals())

    >>> # Return DSN configuration
    >>> options = raven.load(dsn)
    """
    url = urlparse.urlparse(dsn)
    if url.scheme not in ('http', 'https', 'udp'):
        raise ValueError('Unsupported Sentry DSN scheme: %r' % url.scheme)
    netloc = url.hostname
    if url.port and url.port != 80:
        netloc += ':%s' % url.port
    path_bits = url.path.rsplit('/', 1)
    if len(path_bits) > 1:
        path = path_bits[0]
    else:
        path = ''
    project = path_bits[-1]
    if scope is None:
        scope = {}
    if not all([netloc, project, url.username, url.password]):
        raise ValueError('Invalid Sentry DSN: %r' % dsn)
    scope.update({
        'SENTRY_SERVERS': ['%s://%s%s/api/store/' % (url.scheme, netloc, path)],
        'SENTRY_PROJECT': project,
        'SENTRY_PUBLIC_KEY': url.username,
        'SENTRY_SECRET_KEY': url.password,
    })
    return scope


def setup_logging(handler, exclude=['raven', 'gunicorn', 'south', 'sentry.errors']):
    """
    Configures logging to pipe to Sentry.

    - ``exclude`` is a list of loggers that shouldn't go to Sentry.

    For a typical Python install:

    >>> from raven.handlers.logging import SentryHandler
    >>> client = Sentry(...)
    >>> setup_logging(SentryHandler(client))

    Within Django:

    >>> from raven.contrib.django.logging import SentryHandler
    >>> setup_logging(SentryHandler())

    Returns a boolean based on if logging was configured or not.
    """
    logger = logging.getLogger()
    if handler.__class__ in map(type, logger.handlers):
        return False

    logger.addHandler(handler)

    # Add StreamHandler to sentry's default so you can catch missed exceptions
    for logger_name in exclude:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())

    return True
