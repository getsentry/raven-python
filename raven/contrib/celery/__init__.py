"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

try:
    from celery.task import task
except ImportError:
    from celery.decorators import task
from celery.signals import after_setup_logger, task_failure
from raven.base import Client
from raven.handlers.logging import SentryHandler


class CeleryMixin(object):
    def send_encoded(self, *args, **kwargs):
        "Errors through celery"
        self.send_raw.delay(*args, **kwargs)

    @task(routing_key='sentry')
    def send_raw(self, *args, **kwargs):
        return super(CeleryMixin, self).send_encoded(*args, **kwargs)


class CeleryClient(CeleryMixin, Client):
    pass


class CeleryFilter(object):
    def filter(self, record):
        if record.funcName in ('_log_error',):
            return 0
        else:
            return 1


def register_signal(client):
    def process_failure_signal(sender, task_id, exception, args, kwargs,
                               traceback, einfo, **kw):
        client.captureException(
            exc_info=einfo.exc_info,
            extra={
                'task_id': task_id,
                'task': sender,
                'args': args,
                'kwargs': kwargs,
            })
    task_failure.connect(process_failure_signal, weak=False)

    def process_logger_event(sender, logger, loglevel, logfile, format,
                             colorize, **kw):
        import logging
        logger = logging.getLogger()
        handler = SentryHandler(client)
        if handler.__class__ in map(type, logger.handlers):
            return False
        handler.setLevel(logging.ERROR)
        handler.addFilter(CeleryFilter())
        logger.addHandler(handler)
    after_setup_logger.connect(process_logger_event, weak=False)
