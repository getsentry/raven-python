"""
raven.context
~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from collections import Mapping, Iterable
from threading import local
from weakref import ref as weakref

from raven._compat import iteritems


_active_contexts = local()


def get_active_contexts():
    """Returns all the active contexts for the current thread."""
    try:
        return list(_active_contexts.contexts)
    except AttributeError:
        return []


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

    def __init__(self, client=None):
        if client is not None:
            client = weakref(client)
        self._client = client
        self.data = {}
        self.exceptions_to_skip = set()
        self.breadcrumbs = raven.breadcrumbs.BreadcrumbBuffer()

    @property
    def client(self):
        if self._client is None:
            return None
        return self._client()

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.data)

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.deactivate()

    def activate(self):
        _active_contexts.__dict__.setdefault('contexts', set()).add(self)

    def deactivate(self):
        try:
            _active_contexts.contexts.discard(self)
        except AttributeError:
            pass

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

    def clear(self, deactivate=True):
        self.data = {}
        self.exceptions_to_skip.clear()
        self.breadcrumbs.clear()
        if deactivate:
            self.deactivate()


import raven.breadcrumbs
