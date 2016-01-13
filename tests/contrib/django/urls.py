from __future__ import absolute_import

from django.conf import settings
try:
    from django.conf.urls import url
except ImportError:
    # for Django version less than 1.4
    from django.conf.urls.defaults import url  # NOQA

from django.http import HttpResponse


def handler404(request):
    return HttpResponse('', status=404)


def handler500(request):
    if getattr(settings, 'BREAK_THAT_500', False):
        raise ValueError('handler500')
    return HttpResponse('', status=500)


urlpatterns = [
    url(r'^no-error$', 'tests.contrib.django.views.no_error', name='sentry-no-error'),
    url(r'^fake-login$', 'tests.contrib.django.views.fake_login', name='sentry-fake-login'),
    url(r'^trigger-500$', 'tests.contrib.django.views.raise_exc', name='sentry-raise-exc'),
    url(r'^trigger-500-ioerror$', 'tests.contrib.django.views.raise_ioerror', name='sentry-raise-ioerror'),
    url(r'^trigger-500-decorated$', 'tests.contrib.django.views.decorated_raise_exc', name='sentry-raise-exc-decor'),
    url(r'^trigger-500-django$', 'tests.contrib.django.views.django_exc', name='sentry-django-exc'),
    url(r'^trigger-500-template$', 'tests.contrib.django.views.template_exc', name='sentry-template-exc'),
    url(r'^trigger-500-log-request$', 'tests.contrib.django.views.logging_request_exc', name='sentry-log-request-exc'),
]
