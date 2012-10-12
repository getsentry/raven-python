"""
raven.transport.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""


class InvalidScheme(ValueError):
    """
    Raised when a transport is constructed using a URI which is not
    handled by the transport
    """


class DuplicateScheme(StandardError):
    """
    Raised when registering a handler for a particular scheme which
    is already registered
    """
