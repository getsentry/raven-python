WSGI Middleware
===============

Raven includes a simple to use WSGI middleware.

::

    from raven import Client
    from raven.middleware import Sentry

    application = Sentry(
        application,
        Client('___DSN___')
    )

.. note:: Many frameworks will not propagate exceptions to the underlying WSGI middleware by default.
