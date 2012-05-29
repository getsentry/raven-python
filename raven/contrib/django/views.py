"""
raven.contrib.django.views
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import simplejson

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from functools import wraps
from raven.contrib.django.models import client


def is_valid_origin(origin):
    if not settings.SENTRY_ALLOW_ORIGIN:
        return False

    if settings.SENTRY_ALLOW_ORIGIN == '*':
        return True

    if not origin:
        return False

    origin = origin.lower()
    for value in settings.SENTRY_ALLOW_ORIGIN:
        if isinstance(value, basestring):
            if value.lower() == origin:
                return True
        else:
            if value.match(origin):
                return True

    return False


def with_origin(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        origin = request.META.get('HTTP_ORIGIN')

        if not is_valid_origin(origin):
            return HttpResponseForbidden()

        response = func(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'

        return response
    return wrapped


def extract_auth_vars(request):
    """
    raven-js will pass both Authorization and X-Sentry-Auth depending on the browser
    and server configurations.
    """
    if request.META.get('HTTP_X_SENTRY_AUTH', '').startswith('Sentry'):
        return request.META['HTTP_X_SENTRY_AUTH']
    elif request.META.get('HTTP_AUTHORIZATION', '').startswith('Sentry'):
        return request.META['HTTP_AUTHORIZATION']
    else:
        return None


@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
@never_cache
@with_origin
def report(request, project_id=None):
    if request.method == 'POST':
        data = request.raw_post_data
        if not data:
            return HttpResponseBadRequest()

        try:
            decoded = simplejson.loads(data)
        except simplejson.JSONDecodeError:
            return HttpResponseBadRequest()

        response = HttpResponse()
        client.send(auth_header=extract_auth_vars(request), **decoded)

    elif request.method == 'OPTIONS':
        response = HttpResponse()

    return response
