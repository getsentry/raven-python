"""
raven.contrib.django.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from raven.contrib.celery import make_celery_client_class
from raven.contrib.django import DjangoClient

CeleryClient = make_celery_client_class(DjangoClient)