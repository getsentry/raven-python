Configuring ``logbook``
=======================

Raven provides a logbook handler which will pipe messages to Sentry::

::

    from raven.handlers.logbook import SentryHandler

    client = Client(...)
    sentry_handler = SentryHandler(client)
    with my_handler.applicationbound():
        # everything logged here will go to sentry.
