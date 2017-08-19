from __future__ import absolute_import

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from raven.contrib.django.models import client

import logging


class AppError(Exception):
    pass


def no_error(request):
    return HttpResponse('')


def fake_login(request):
    return HttpResponse('')


def django_exc(request):
    return get_object_or_404(Exception, pk=1)


def raise_exc(request):
    raise Exception(request.GET.get('message', 'view exception'))


def read_request_and_raise_exc(request):
    request.read()
    raise AppError()


def raise_ioerror(request):
    raise IOError(request.GET.get('message', 'view exception'))


def decorated_raise_exc(request):
    return raise_exc(request)


def template_exc(request):
    return render_to_response('error.html')


def logging_request_exc(request):
    logger = logging.getLogger(__name__)
    try:
        raise Exception(request.GET.get('message', 'view exception'))
    except Exception as e:
        logger.error(e, exc_info=True, extra={'request': request})
    return HttpResponse('')


def capture_event(request):
    client.captureMessage('test')
    return HttpResponse('')
