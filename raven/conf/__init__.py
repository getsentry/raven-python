"""
raven.conf
~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging
from raven.utils.urlparse import urlparse

__all__ = ('load', 'setup_logging')

EXCLUDE_LOGGER_DEFAULTS = (
    'raven',
    'gunicorn',
    'south',
    'sentry.errors',
    'django.request',
)


# TODO (vng): this seems weirdly located in raven.conf.  Seems like
# it's really a part of raven.transport.TransportRegistry
# Not quite sure what to do with this
def load(dsn, scope=None, transport_registry=None):
    """
    Parses a Sentry compatible DSN and loads it
    into the given scope.

    >>> import raven

    >>> dsn = 'https://public_key:secret_key@sentry.local/project_id'

    >>> # Apply configuration to local scope
    >>> raven.load(dsn, locals())

    >>> # Return DSN configuration
    >>> options = raven.load(dsn)
    """

    if not transport_registry:
        from raven.transport import TransportRegistry, default_transports
        transport_registry = TransportRegistry(default_transports)

    url = urlparse(dsn)

    if not transport_registry.supported_scheme(url.scheme):
        raise ValueError('Unsupported Sentry DSN scheme: %r' % url.scheme)

    if scope is None:
        scope = {}
    scope_extras = transport_registry.compute_scope(url, scope)
    scope.update(scope_extras)

    return scope


def setup_logging(handler, exclude=EXCLUDE_LOGGER_DEFAULTS):
    """
    Configures logging to pipe to Sentry.

    - ``exclude`` is a list of loggers that shouldn't go to Sentry.

    For a typical Python install:

    >>> from raven.handlers.logging import SentryHandler
    >>> client = Sentry(...)
    >>> setup_logging(SentryHandler(client))

    Within Django:

    >>> from raven.contrib.django.handlers import SentryHandler
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
