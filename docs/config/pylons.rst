Configuring Pylons
==================

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
    args = (['http://sentry.local/api/store/'], 'KEY')
    level = NOTSET
    formatter = generic

    [formatter_generic]
    format = %(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %H:%M:%S

.. note:: You may want to setup other loggers as well.


