Configuring ``logging``
=======================

Sentry supports the ability to directly tie into the ``logging`` module. To use it simply add ``SentryHandler`` to your logger.

::

    import logging
    from raven import Client
    from raven.handlers.logging import SentryHandler

    client = Client(remote_urls=['http://sentry.local/store/'], key='MY SECRET KEY')
    logger = logging.getLogger()

    # ensure we havent already registered the handler
    if SentryHandler not in map(type, logger.handlers):
        logger.addHandler(SentryHandler(client))

        # Add StreamHandler to sentry's default so you can catch missed exceptions
        logger = logging.getLogger('sentry.errors')
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())

Usage
~~~~~

A recommended pattern in logging is to simply reference the modules name for each logger, so for example, you might at the top of your module define the following::

    import logging
    logger = logging.getLogger(__name__)

You can also use the ``exc_info`` and ``extra=dict(url=foo)`` arguments on your ``log`` methods. This will store the appropriate information and allow django-sentry to render it based on that information::

    logger.error('There was some crazy error', exc_info=True, extra={'url': request.build_absolute_uri()})

You may also pass additional information to be stored as meta information with the event. As long as the key
name is not reserved and not private (_foo) it will be displayed on the Sentry dashboard. To do this, pass it as ``data`` within
your ``extra`` clause::

    logger.error('There was some crazy error', exc_info=True, extra={
        # Optionally you can pass additional arguments to specify request info
        'view': 'my.view.name',
        'url': request.build_absolute_url(),

        'data': {
            # You may specify any values here and Sentry will log and output them
            'username': request.user.username
        }
    })

.. note:: The ``url`` and ``view`` keys are used internally by Sentry within the extra data.
.. note:: Any key (in ``data``) prefixed with ``_`` will not automatically output on the Sentry details view.

Sentry will intelligently group messages if you use proper string formatting. For example, the following messages would
be seen as the same message within Sentry::

    logger.error('There was some %s error', 'crazy')
    logger.error('There was some %s error', 'fun')
    logger.error('There was some %s error', 1)

As of Sentry 1.10.0 the ``logging`` integration also allows easy capture of stack frames (and their locals) as if you were
logging an exception. This can be done automatically with the ``SENTRY_AUTO_LOG_STACKS`` setting, as well as by passing the
``stack`` boolean to ``extra``::

    logger.error('There was an error', extra={'stack': True})

.. note::

    We are describing a client/server interaction where
    both components are provided by django-sentry.  Other languages that
    provide a logging package that is comparable to the python ``logging``
    package may define a sentry handler.  Check the:ref:`Extending Sentry <extending-sentry>`
    documentation.