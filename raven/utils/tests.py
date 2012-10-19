"""
raven.utils.tests
~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from functools import wraps
from nose.plugins.skip import SkipTest

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


def requires(condition, msg=None):
    """
    >>> class Foo(object):
    >>>     @requires(lambda x: sys.version_info >= (2, 6, 0))
    >>>     def foo(self):
    >>>         # do something that doesnt work on py2.5
    >>>         pass
    """
    def wrapped(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if not condition:
                raise SkipTest(msg or '')
            return func
        return inner
    return wrapped
