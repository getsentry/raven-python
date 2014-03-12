"""
raven.context
~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from collections import Mapping, Iterable
from threading import local

from raven.utils import six


class Context(local, Mapping, Iterable):
    """
    Stores context until cleared.

    >>> def view_handler(view_func, *args, **kwargs):
    >>>     context = Context()
    >>>     context.merge(tags={'key': 'value'})
    >>>     try:
    >>>         return view_func(*args, **kwargs)
    >>>     finally:
    >>>         context.clear()
    """
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.data)

    def merge(self, data):
        d = self.data
        for key, value in six.iteritems(data):
            if key in ('tags', 'extra'):
                d.setdefault(key, {})
                for t_key, t_value in six.iteritems(value):
                    d[key][t_key] = t_value
            else:
                d[key] = value

    def set(self, data):
        self.data = data

    def get(self):
        return self.data

    def clear(self):
        self.data = {}
