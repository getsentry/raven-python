from __future__ import absolute_import

import celery
import logging

from raven.contrib.celery import (
    SentryCeleryHandler,
    register_logger_signal,
    CeleryFilter
)
from raven.handlers.logging import SentryHandler
from raven.utils.testutils import InMemoryClient, TestCase


class CeleryTestCase(TestCase):
    def setUp(self):
        super(CeleryTestCase, self).setUp()
        self.celery = celery.Celery(__name__)
        self.celery.conf.CELERY_ALWAYS_EAGER = True

        self.client = InMemoryClient()
        self.handler = SentryCeleryHandler(self.client, ignore_expected=True)
        self.handler.install()
        self.addCleanup(self.handler.uninstall)

    def test_simple(self):
        @self.celery.task(name='dummy_task')
        def dummy_task(x, y):
            return x / y

        dummy_task.delay(1, 2)
        dummy_task.delay(1, 0)
        assert len(self.client.events) == 1
        event = self.client.events[0]
        exception = event['exception']['values'][-1]
        assert event['transaction'] == 'dummy_task'
        assert exception['type'] == 'ZeroDivisionError'

    def test_ignore_expected(self):
        @self.celery.task(name='dummy_task', throws=(ZeroDivisionError,))
        def dummy_task(x, y):
            return x / y

        dummy_task.delay(1, 2)
        dummy_task.delay(1, 0)
        assert len(self.client.events) == 0


class CeleryLoggingHandlerTestCase(TestCase):
    def setUp(self):
        super(CeleryLoggingHandlerTestCase, self).setUp()

        self.client = InMemoryClient()

        # register the logger signal
        # and unregister the signal when the test is done
        register_logger_signal(self.client)
        receiver = celery.signals.after_setup_logger.receivers[0][1]
        self.addCleanup(celery.signals.after_setup_logger.disconnect, receiver)

        # remove any existing handlers and restore
        # them when complete
        self.root = logging.getLogger()
        for handler in self.root.handlers:
            self.root.removeHandler(handler)
            self.addCleanup(self.root.addHandler, handler)

    def test_handler_added(self):
        # Given: there are no handlers configured
        assert not self.root.handlers

        # When: the after_setup_logger signal is sent
        celery.signals.after_setup_logger.send(
            sender=None, logger=self.root,
            loglevel=logging.WARNING, logfile=None,
            format=u'', colorize=False,
        )

        # Then: there is 1 new handler
        assert len(self.root.handlers) == 1

        # Then: the new handler is an instance of
        # `raven.handlers.logging.SentryHandler`
        handler = self.root.handlers[0]
        assert isinstance(handler, SentryHandler)

        # Then: the handler has 1 filter
        assert len(handler.filters) == 1

        # Then: the filter is a CeleryFilter
        _filter = handler.filters[0]
        assert isinstance(_filter, CeleryFilter)

        # set up the handler to be removed once the test is done
        self.addCleanup(self.root.removeHandler, handler)

    def test_handler_updated(self):

        # Given: there is 1 preconfigured SentryHandler
        # with no filters
        handler = SentryHandler(self.client)
        assert not handler.filters
        self.root.addHandler(handler)
        # set up the handler to be removed once the test is done
        self.addCleanup(self.root.removeHandler, handler)

        # When: the after_setup_logger signal is sent
        celery.signals.after_setup_logger.send(
            sender=None, logger=self.root,
            loglevel=logging.WARNING, logfile=None,
            format=u'', colorize=False,
        )

        # Then: there is still just 1 handler
        assert len(self.root.handlers) == 1

        # Then: the existing handler is an instance of
        # `raven.handlers.logging.SentryHandler`
        handler = self.root.handlers[0]
        assert isinstance(handler, SentryHandler)

        # Then: the existing handler has 1 filter
        assert len(handler.filters) == 1

        # Then: the filter is a CeleryFilter
        _filter = handler.filters[0]
        assert isinstance(_filter, CeleryFilter)

    def test_subclassed_handler_updated(self):

        # Given: there is 1 preconfigured CustomHandler
        # with no filters
        class CustomHandler(SentryHandler):
            pass

        handler = CustomHandler(self.client)
        assert not handler.filters
        self.root.addHandler(handler)
        # set up the handler to be removed once the test is done
        self.addCleanup(self.root.removeHandler, handler)

        # When: the after_setup_logger signal is sent
        celery.signals.after_setup_logger.send(
            sender=None, logger=self.root,
            loglevel=logging.WARNING, logfile=None,
            format=u'', colorize=False,
        )

        # Then: there is still just 1 handler
        assert len(self.root.handlers) == 1

        # Then: the existing handler is an instance of
        # `CustomHandler`
        handler = self.root.handlers[0]
        assert isinstance(handler, CustomHandler)

        # Then: the existing handler has 1 filter
        assert len(handler.filters) == 1

        # Then: the filter is a CeleryFilter
        _filter = handler.filters[0]
        assert isinstance(_filter, CeleryFilter)
