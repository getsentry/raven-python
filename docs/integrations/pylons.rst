Pylons
======

WSGI Middleware
---------------

A Pylons-specific middleware exists to enable easy configuration from settings:

::

    from raven.contrib.pylons import Sentry

    application = Sentry(application, config)

Configuration is handled via the sentry namespace:

.. code-block:: ini

    [sentry]
    dsn=http://public:secret@example.com/1
    include_paths=my.package,my.other.package,
    exclude_paths=my.package.crud


Logger setup
------------

Add the following lines to your project's `.ini` file to setup `SentryHandler`:

.. code-block:: ini

    [loggers]
    keys = root, sentry

    [handlers]
    keys = console, sentry

    [formatters]
    keys = generic

    [logger_root]
    level = INFO
    handlers = console, sentry

    [logger_sentry]
    level = WARN
    handlers = console
    qualname = sentry.errors
    propagate = 0

    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = generic

    [handler_sentry]
    class = raven.handlers.logging.SentryHandler
    args = ('SENTRY_DSN',)
    level = NOTSET
    formatter = generic

    [formatter_generic]
    format = %(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %H:%M:%S

.. note:: You may want to setup other loggers as well.


