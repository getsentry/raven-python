"""
raven.context
~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import time

from collections import Mapping, Iterable
from datetime import datetime
from threading import local

from raven._compat import iteritems


class BreadcrumbBuffer(object):

    def __init__(self, limit=100):
        self.buffer = []
        self.limit = limit

    def record(self, type, data=None, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        elif isinstance(timestamp, datetime):
            timestamp = datetime

        self.buffer.append({
            'type': type,
            'timestamp': timestamp,
            'data': data or {},
        })
        del self.buffer[:-self.limit]

    def clear(self):
        del self.buffer[:]


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
        self.exceptions_to_skip = set()

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
        for key, value in iteritems(data):
            if key in ('tags', 'extra'):
                d.setdefault(key, {})
                for t_key, t_value in iteritems(value):
                    d[key][t_key] = t_value
            else:
                d[key] = value

    def set(self, data):
        self.data = data

    def get(self):
        return self.data

    def clear(self):
        self.data = {}
        self.exceptions_to_skip.clear()
