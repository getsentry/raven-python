"""
raven.contrib.django.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from raven.contrib.celery import CeleryMixin
from raven.contrib.django import DjangoClient
from raven.contrib.django.models import get_client
try:
    from celery.task import task
except ImportError:
    from celery.decorators import task  # NOQA


class CeleryClient(CeleryMixin, DjangoClient):

    def send_integrated(self, kwargs):
        return send_raw_integrated.delay(kwargs)

    def send_encoded(self, *args, **kwargs):
        "Errors through celery"
        return send_raw.delay(*args, **kwargs)


@task(routing_key='sentry')
def send_raw_integrated(kwargs):
    super(DjangoClient, get_client()).send_integrated(kwargs)


@task(routing_key='sentry')
def send_raw(*args, **kwargs):
    super(DjangoClient, get_client()).send_encoded(*args, **kwargs)
