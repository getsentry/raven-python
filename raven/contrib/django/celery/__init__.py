"""
raven.contrib.django.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.conf import settings
from celery.decorators import task
from raven.contrib.django import DjangoClient
from raven.contrib.django.models import get_client

queue=getattr(settings, 'SENTRY_CELERY_QUEUE', 'celery')

@task(queue=queue)
def send_remote(kwargs):
    '''Send log to the sentry server, synchronously'''
    get_client().send(async=False, **kwargs)

class CeleryClient(DjangoClient):
    def send(self, async=True, **kwargs):
        '''Send log to the sentry server'''

        if async:
            # Schedule the job via a task
            send_remote.delay(kwargs)
        else:
            super(DjangoClient, self).send(**kwargs)

