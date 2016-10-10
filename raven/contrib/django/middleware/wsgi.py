"""
raven.contrib.django.middleware.wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object

from raven.middleware import Sentry
from raven.utils import memoize


class Sentry(Sentry, MiddlewareMixin):
    """
    Identical to the default WSGI middleware except that
    the client comes dynamically via ``get_client

    >>> from raven.contrib.django.middleware.wsgi import Sentry
    >>> application = Sentry(application)
    """
    def __init__(self, application):
        self.application = application

    @memoize
    def client(self):
        from raven.contrib.django.models import client
        return client
