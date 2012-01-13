Configuring ``wsgi`` Middleware
===============================

Raven includes a simple to use wsgi middleware.

::

    from raven import Client
    from raven.middleware import Sentry

    application = Sentry(application, Client(
        servers=['http://sentry.local/api/store/'],
        key='my secret key'
    )

.. note:: Many frameworks will not propagate exceptions to the underlying WSGI middleware by default.
