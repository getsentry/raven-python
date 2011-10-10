from __future__ import absolute_import

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^fake-login$', 'tests.contrib.django.views.fake_login', name='sentry-fake-login'),
    url(r'^trigger-500$', 'tests.contrib.django.views.raise_exc', name='sentry-raise-exc'),
    url(r'^trigger-500-decorated$', 'tests.contrib.django.views.decorated_raise_exc', name='sentry-raise-exc-decor'),
    url(r'^trigger-500-django$', 'tests.contrib.django.views.django_exc', name='sentry-django-exc'),
    url(r'^trigger-500-template$', 'tests.contrib.django.views.template_exc', name='sentry-template-exc'),
    url(r'^trigger-500-log-request$', 'tests.contrib.django.views.logging_request_exc', name='sentry-log-request-exc'),
)