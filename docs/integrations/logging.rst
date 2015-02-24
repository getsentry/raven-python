Logging
=======

Sentry supports the ability to directly tie into the :mod:`logging` module.  To
use it simply add :class:`SentryHandler` to your logger.

First you'll need to configure a handler::

    from raven.handlers.logging import SentryHandler

    # Manually specify a client
    client = Client(...)
    handler = SentryHandler(client)

You can also automatically configure the default client with a DSN::

    # Configure the default client
    handler = SentryHandler('http://public:secret@example.com/1')

Finally, call the :func:`setup_logging` helper function::

    from raven.conf import setup_logging

    setup_logging(handler)

Another option is to use :mod:`logging.config.dictConfig`::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,

        'formatters': {
            'console': {
                'format': '[%(asctime)s][%(levelname)s] %(name)s %(filename)s:%(funcName)s:%(lineno)d | %(message)s',
                'datefmt': '%H:%M:%S',
                },
            },

        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console'
                },
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.handlers.logging.SentryHandler',
                'dsn': 'http://public:secret@example.com/1',
                },
            },

        'loggers': {
            '': {
                'handlers': ['console', 'sentry'],
                'level': 'DEBUG',
                'propagate': False,
                },
            'your_app': {
                'level': 'DEBUG',
                'propagate': True,
            },
        }
    }

Usage
~~~~~

A recommended pattern in logging is to simply reference the modules name for
each logger, so for example, you might at the top of your module define the
following::

    import logging
    logger = logging.getLogger(__name__)

You can also use the ``exc_info`` and ``extra={'stack': True}`` arguments on
your ``log`` methods. This will store the appropriate information and allow
Sentry to render it based on that information::

    # If you're actually catching an exception, use `exc_info=True`
    logger.error('There was an error, with a stacktrace!', exc_info=True)

    # If you don't have an exception, but still want to capture a stacktrace, use the `stack` arg
    logger.error('There was an error, with a stacktrace!', extra={
        'stack': True,
    })

.. note:: Depending on the version of Python you're using, ``extra`` might not be an acceptable keyword argument for a logger's ``.exception()`` method (``.debug()``, ``.info()``, ``.warning()``, ``.error()`` and ``.critical()`` should work fine regardless of Python version). This should be fixed as of Python 3.2. Official issue here: http://bugs.python.org/issue15541.

While we don't recommend this, you can also enable implicit stack capturing for all messages::

    client = Client(..., auto_log_stacks=True)
    handler = SentryHandler(client)

    logger.error('There was an error, with a stacktrace!')

You may also pass additional information to be stored as meta information with
the event. As long as the key name is not reserved and not private (_foo) it
will be displayed on the Sentry dashboard. To do this, pass it as ``data``
within your ``extra`` clause::

    logger.error('There was some crazy error', exc_info=True, extra={
        # Optionally you can pass additional arguments to specify request info
        'culprit': 'my.view.name',

        'data': {
            # You may specify any values here and Sentry will log and output them
            'username': request.user.username,
        }
    })

.. note:: The ``url`` and ``view`` keys are used internally by Sentry within the extra data.
.. note:: Any key (in ``data``) prefixed with ``_`` will not automatically output on the Sentry details view.

Sentry will intelligently group messages if you use proper string formatting. For example, the following messages would
be seen as the same message within Sentry::

    logger.error('There was some %s error', 'crazy')
    logger.error('There was some %s error', 'fun')
    logger.error('There was some %s error', 1)

.. note::

    Other languages that provide a logging package that is comparable to the
    python :mod:`logging` package may define a Sentry handler.  Check the
    `Extending Sentry
    <http://sentry.readthedocs.org/en/latest/developer/client/index.html>`_
    documentation.
