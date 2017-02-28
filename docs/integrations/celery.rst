Celery
======

`Celery <http://www.celeryproject.org/>`_ is a distributed task queue
system for Python built on AMQP principles.  For Celery built-in support
by Raven is provided but it requires some manual configuration.

To capture errors, you need to register a couple of signals to hijack
Celery error handling::

    from raven import Client
    from raven.contrib.celery import register_signal, register_logger_signal

    client = Client('___DSN___')

    # register a custom filter to filter out duplicate logs
    register_logger_signal(client)

    # The register_logger_signal function can also take an optional argument
    # `loglevel` which is the level used for the handler created.
    # Defaults to `logging.ERROR`
    register_logger_signal(client, loglevel=logging.INFO)

    # hook into the Celery error handler
    register_signal(client)

    # The register_signal function can also take an optional argument
    # `ignore_expected` which causes exception classes specified in Task.throws
    # to be ignored
    register_signal(client, ignore_expected=True)

A more complex version to encapsulate behavior:

.. code-block:: python

    import celery
    import raven
    from raven.contrib.celery import register_signal, register_logger_signal

    class Celery(celery.Celery):

        def on_configure(self):
            client = raven.Client('___DSN___')

            # register a custom filter to filter out duplicate logs
            register_logger_signal(client)

            # hook into the Celery error handler
            register_signal(client)

    app = Celery(__name__)
    app.config_from_object('django.conf:settings')
