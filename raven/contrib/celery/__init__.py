"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
from celery.signals import after_setup_logger, task_failure
from raven.handlers.logging import SentryHandler


class CeleryFilter(logging.Filter):
    def filter(self, record):
        # celery.redirected is used for stdout -- kill it
        # TODO(dcramer): this should be more configurable, but our default
        # injections with Celery aren't super friendly towards configurability
        if record.name == 'celery.redirected':
            return False

        # Context is fixed in Celery 3.x so use internal flag instead
        extra_data = getattr(record, 'data', {})
        if not isinstance(extra_data, dict):
            return record.funcName != '_log_error'
        # Fallback to funcName for Celery 2.5
        return extra_data.get('internal', record.funcName != '_log_error')


def register_signal(client):
    def process_failure_signal(sender, task_id, args, kwargs, **kw):
        # This signal is fired inside the stack so let raven do its magic
        client.captureException(
            extra={
                'task_id': task_id,
                'task': sender,
                'args': args,
                'kwargs': kwargs,
            })

    task_failure.connect(process_failure_signal, weak=False)


def register_logger_signal(client, logger=None, loglevel=logging.ERROR):
    # logger is unused
    register_logging_filter(client)
    register_logger(client, loglevel)


def register_logging_filter(client):
    def sentry_logging_filter(sender, logger, loglevel, logfile, format,
                             colorize, **kw):
        # Attempt to find an existing SentryHandler, and if it exists ensure
        # that the CeleryFilter is installed.
        # If one is found, we do not attempt to install another one.
        for h in logger.handlers:
            if type(h) == SentryHandler:
                filter_ = CeleryFilter()
                h.addFilter(filter_)
                return False

    after_setup_logger.connect(sentry_logging_filter, weak=False)


def register_logger(client, loglevel=logging.ERROR):
    def sentry_logger(sender, logger, loglevel, logfile, format,
                      colorize, **kw):
        filter_ = CeleryFilter()
        handler = SentryHandler(client)
        handler.setLevel(loglevel)
        handler.addFilter(filter_)
        logger.addHandler(handler)

    after_setup_logger.connect(sentry_logger, weak=False)
