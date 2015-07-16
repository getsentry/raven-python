Logbook
=======

Raven provides a `logbook <http://logbook.pocoo.org>`_ handler which will pipe
messages to Sentry.

First you'll need to configure a handler::

    from raven.handlers.logbook import SentryHandler

    # Manually specify a client
    client = Client(...)
    handler = SentryHandler(client)

You can also automatically configure the default client with a DSN::

    # Configure the default client
    handler = SentryHandler('___DSN___')

Finally, bind your handler to your context::

    from raven.handlers.logbook import SentryHandler

    client = Client(...)
    sentry_handler = SentryHandler(client)
    with sentry_handler.applicationbound():
        # everything logged here will go to sentry.
        ...
