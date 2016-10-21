"""
raven.contrib.django.middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
import threading

from django.conf import settings
from django.core.signals import request_finished

try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object

from raven.contrib.django.resolver import RouteResolver


def is_ignorable_404(uri):
    """
    Returns True if a 404 at the given URL *shouldn't* notify the site managers.
    """
    return any(
        pattern.search(uri)
        for pattern in getattr(settings, 'IGNORABLE_404_URLS', ())
    )


class Sentry404CatchMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response

        if is_ignorable_404(request.get_full_path()):
            return response

        from raven.contrib.django.models import client

        if not client.is_enabled():
            return response

        data = client.get_data_from_request(request)
        data.update({
            'level': logging.INFO,
            'logger': 'http404',
        })
        result = client.captureMessage(message='Page Not Found: %s' % request.build_absolute_uri(), data=data)
        if not result:
            return

        request.sentry = {
            'project_id': data.get('project', client.remote.project),
            'id': client.get_ident(result),
        }
        return response

    # sentry_exception_handler(sender=Sentry404CatchMiddleware, request=request)


class SentryResponseErrorIdMiddleware(MiddlewareMixin):
    """
    Appends the X-Sentry-ID response header for referencing a message within
    the Sentry datastore.
    """
    def process_response(self, request, response):
        if not getattr(request, 'sentry', None):
            return response
        response['X-Sentry-ID'] = request.sentry['id']
        return response


# We need to make a base class for our sentry middleware that is thread
# local but at the same time has the new fnagled middleware mixin applied
# if such a thing exists.
if MiddlewareMixin is object:
    _SentryMiddlewareBase = threading.local
else:
    _SentryMiddlewareBase = type('_SentryMiddlewareBase', (MiddlewareMixin, threading.local), {})


class SentryMiddleware(_SentryMiddlewareBase):
    resolver = RouteResolver()

    # backwards compat
    @property
    def thread(self):
        return self

    def _get_transaction_from_request(self, request):
        # TODO(dcramer): it'd be nice to pull out parameters
        # and make this a normalized path
        return self.resolver.resolve(request.path)

    def process_request(self, request):
        self._txid = None
        self.thread.request = request

    def process_view(self, request, func, args, kwargs):
        from raven.contrib.django.models import client

        try:
            self._txid = client.transaction.push(
                self._get_transaction_from_request(request)
            )
        except Exception as exc:
            client.error_logger.exception(repr(exc))
        else:
            # we utilize request_finished as the exception gets reported
            # *after* process_response is executed, and thus clearing the
            # transaction there would leave it empty
            # XXX(dcramer): weakref's cause a threading issue in certain
            # versions of Django (e.g. 1.6). While they'd be ideal, we're under
            # the assumption that Django will always call our function except
            # in the situation of a process or thread dying.
            request_finished.connect(self.request_finished, weak=False)

        return None

    def request_finished(self, **kwargs):
        from raven.contrib.django.models import client

        if getattr(self, '_txid', None):
            client.transaction.pop(self._txid)
            self._txid = None

        request_finished.disconnect(self.request_finished)

SentryLogMiddleware = SentryMiddleware
