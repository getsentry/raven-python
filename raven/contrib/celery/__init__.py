"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging
try:
    from celery.task import task
except ImportError:
    from celery.decorators import task  # NOQA
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


class CeleryFilter(logging.Filter):
    def filter(self, record):
        return record.funcName not in ('_log_error',)


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


def register_logger_signal(client, logger=None):
    filter_ = CeleryFilter()

    if logger is None:
        logger = logging.getLogger()
        handler = SentryHandler(client)
        handler.setLevel(logging.ERROR)
        handler.addFilter(filter_)

    def process_logger_event(sender, logger, loglevel, logfile, format,
                             colorize, **kw):
        # Attempt to find an existing SentryHandler, and if it exists ensure
        # that the CeleryFilter is installed.
        # If one is found, we do not attempt to install another one.
        for h in logger.handlers:
            if type(h) == SentryHandler:
                if not any(type(f) == CeleryFilter for f in h.filters):
                    h.addFilter(filter_)
                return False

        logger.addHandler(handler)

    after_setup_logger.connect(process_logger_event, weak=False)
