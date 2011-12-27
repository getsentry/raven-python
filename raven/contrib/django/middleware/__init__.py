"""
raven.contrib.django.middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from django.middleware.common import _is_ignorable_404
from raven.contrib.django.models import get_client
import threading
import logging

class Sentry404CatchMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404 or _is_ignorable_404(request.get_full_path()):
            return response
        client = get_client()
        data = client.get_data_from_request(request)
        data.update({
            'level': logging.INFO,
            'logger': 'http404',
        })
        result = client.capture('Message', message='Page Not Found: %s' % request.build_absolute_uri(), data=data)
        request.sentry = {
            'project_id': data.get('project', client.project),
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

class SentryLogMiddleware(object):
    # Create a threadlocal variable to store the session in for logging
    thread = threading.local()

    def process_request(self, request):
        self.thread.request = request

