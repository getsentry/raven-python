from __future__ import absolute_import

from django.conf import settings
try:
    from django.conf.urls import url, include
except ImportError:
    # for Django version less than 1.4
    from django.conf.urls.defaults import url, include  # NOQA

from django.http import HttpResponse

from tests.contrib.django import views


def handler404(request, exception=None):
    return HttpResponse('', status=404)


def handler500(request, exception=None):
    if getattr(settings, 'BREAK_THAT_500', False):
        raise ValueError('handler500')
    return HttpResponse('', status=500)


urlpatterns = (
    url(r'^no-error$', views.no_error, name='sentry-no-error'),
    url(r'^fake-login$', views.fake_login, name='sentry-fake-login'),
    url(r'^trigger-500$', views.raise_exc, name='sentry-raise-exc'),
    url(r'^trigger-500-readrequest$', views.read_request_and_raise_exc, name='sentry-readrequest-raise-exc'),
    url(r'^trigger-500-ioerror$', views.raise_ioerror, name='sentry-raise-ioerror'),
    url(r'^trigger-500-decorated$', views.decorated_raise_exc, name='sentry-raise-exc-decor'),
    url(r'^trigger-500-django$', views.django_exc, name='sentry-django-exc'),
    url(r'^trigger-500-template$', views.template_exc, name='sentry-template-exc'),
    url(r'^trigger-500-log-request$', views.logging_request_exc, name='sentry-log-request-exc'),
    url(r'^trigger-event$', views.capture_event, name='sentry-trigger-event'),
)

try:
    from tastypie.api import Api
except ImportError:
    pass
else:
    from tests.contrib.django.api import ExampleResource, AnotherExampleResource

    v1_api = Api(api_name='v1')
    v1_api.register(ExampleResource())
    v1_api.register(AnotherExampleResource())

    urlpatterns += (
        url(r'^api/', include(v1_api.urls)),
    )
