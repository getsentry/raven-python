"""
raven.contrib.django.views
~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from raven.contrib.django.models import client


def apply_access_control_headers(response):
    """
    Provides the Access-Control headers to enable cross-site HTTP requests. You
    can find more information about these headers here:
    https://developer.mozilla.org/En/HTTP_access_control#Simple_requests
    """
    origin = settings.SENTRY_ALLOW_ORIGIN or ''
    if origin:
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Headers'] = 'X-Sentry-Auth, Authentication'
        response['Access-Control-Allow-Methods'] = 'POST'

    return response


@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
@never_cache
def report(request):
    data = request.POST.get('data')

    if request.method == 'POST':
        origin = request.META.get('HTTP_ORIGIN')
        if not origin:
            response = HttpResponseForbidden()
        else:
            client.send(data)
    else:
        # OPTIONS
        response = HttpResponse()
    return apply_access_control_headers(response)
