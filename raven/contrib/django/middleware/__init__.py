"""
raven.contrib.django.middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import threading
import logging

from django.conf import settings


def is_ignorable_404(uri):
    """
    Returns True if a 404 at the given URL *shouldn't* notify the site managers.
    """
    return any(
        pattern.search(uri)
        for pattern in getattr(settings, 'IGNORABLE_404_URLS', ())
    )


class Sentry404CatchMiddleware(object):
    def process_response(self, request, response):
        from raven.contrib.django.models import client

        if response.status_code != 404 or is_ignorable_404(request.get_full_path()) or not client.is_enabled():
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


class SentryResponseErrorIdMiddleware(object):
    """
    Appends the X-Sentry-ID response header for referencing a message within
    the Sentry datastore.
    """
    def process_response(self, request, response):
        if not getattr(request, 'sentry', None):
            return response
        response['X-Sentry-ID'] = request.sentry['id']
        return response


class SentryMiddleware(threading.local):
    # backwards compat
    @property
    def thread(self):
        return self

    def _get_transaction_from_view(self, func):
        module = func.__module__.rsplit('.', 1)[-1]
        if hasattr(func, 'im_class'):
            return '{0}.{1}.{2}'.format(
                module,
                func.im_class.__name__,
                func.__name__,
            )
        return '{0}.{1}'.format(
            module,
            func.__name__,
        )

    def process_request(self, request):
        self._txid = None
        self.thread.request = request

    def process_view(self, request, func, args, kwargs):
        from raven.contrib.django.models import client

        try:
            self._txid = client.transaction.push(self._get_transaction_from_view(func))
        except Exception as exc:
            client.error_logger.exception(unicode(exc))
        return None

    def process_response(self, request, response):
        from raven.contrib.django.models import client

        if self._txid:
            client.transaction.pop(self._txid)
            self._txid = None
        return response

    # def process_exception(self, request, exception):
    #     from raven.contrib.django.models import client

    #     if self._txid:
    #         client.transaction.pop(self._txid)
    #         self._txid = None

SentryLogMiddleware = SentryMiddleware
