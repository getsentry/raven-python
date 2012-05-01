"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

try:
    from celery.task import task
except ImportError:
    from celery.decorators import task
from celery.signals import task_failure
from raven.base import Client


class CeleryMixin(object):
    def send_encoded(self, message):
        "Errors through celery"
        self.send_raw.delay(message)

    @task(routing_key='sentry')
    def send_raw(self, message):
        return super(CeleryMixin, self).send_encoded(message)


class CeleryClient(CeleryMixin, Client):
    pass


def register_signal(client):
    def process_failure_signal(exception, traceback, sender, task_id,
                               signal, args, kwargs, einfo, **kw):
        exc_info = (type(exception), exception, traceback)
        client.captureException(
            exc_info=exc_info,
            extra={
                'task_id': task_id,
                'sender': sender,
                'args': args,
                'kwargs': kwargs,
            })
    task_failure.connect(process_failure_signal)
