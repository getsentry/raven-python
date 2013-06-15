"""
raven.context
~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.utils import six


class Context(object):
    """
    Create default context around a block of code for exception management.

    >>> with Context(client, tags={'key': 'value'}) as raven:
    >>>     # use the context manager's client reference
    >>>     raven.captureMessage('hello!')
    >>>
    >>>     # uncaught exceptions also contain the context
    >>>     1 / 0
    """
    def __init__(self, client, **defaults):
        self.client = client
        self.defaults = defaults
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if all(exc_info):
            self.result = self.captureException(exc_info)

    def __call(self, function, *args, **kwargs):
        for key, value in six.iteritems(self.defaults):
            if key not in kwargs:
                kwargs[key] = value

        return function(*args, **kwargs)

    def captureException(self, *args, **kwargs):
        return self.__call(self.client.captureException, *args, **kwargs)

    def captureMessage(self, *args, **kwargs):
        return self.__call(self.client.captureMessage, *args, **kwargs)
