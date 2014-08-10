"""
raven.contrib.django.celery.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from celery import VERSION

djcelery_required = not (VERSION[0] == 3 and VERSION[1] >= 1)

if djcelery_required and 'djcelery' not in settings.INSTALLED_APPS:
    raise ImproperlyConfigured(
        "Put 'djcelery' in your INSTALLED_APPS setting in order to use the "
        "sentry celery client.")
