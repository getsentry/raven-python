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
from raven.contrib.django.models import client


def is_valid_origin(origin):
    if not settings.SENTRY_ALLOW_ORIGIN:
        return False

    if settings.SENTRY_ALLOW_ORIGIN == '*':
        return True

    origin = origin.lower()
    for value in settings.SENTRY_ALLOW_ORIGIN.split(' '):
        if value.lower() == origin:
            return True

    return False


@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
@never_cache
def report(request):
    origin = request.META.get('HTTP_ORIGIN')

    if not is_valid_origin(origin):
        return HttpResponseForbidden()

    if request.method == 'POST':
        data = request.raw_post_data
        if not data:
            return HttpResponseBadRequest()

        try:
            decoded = simplejson.loads(data)
        except simplejson.JSONDecodeError:
            return HttpResponseBadRequest()

        response = HttpResponse()
        client.send(**decoded)

    elif request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'

    return response
