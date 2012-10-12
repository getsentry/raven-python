"""
raven.utils.tests
~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

NOTSET = object()


class fixture(object):
    """
    >>> class Foo(object):
    >>>     @fixture
    >>>     def foo(self):
    >>>         # calculate something important here
    >>>         return 42
    """
    def __init__(self, func):
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, NOTSET)
        if value is NOTSET:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value
