Celery
======

tl;dr register a couple of signals to hijack Celery error handling

.. code-block:: python

    from raven import Client
    from raven.contrib.celery import register_signal, register_logger_signal

    client = Client()

    # register a custom filter to filter out duplicate logs
    register_logger_signal(client)

    # hook into the Celery error handler
    register_signal(client)

    # The register_logger_signal function can also take an optional argument
    # `loglevel` which is the level used for the handler created.
    # Defaults to `logging.ERROR`
    register_logger_signal(client, loglevel=logging.INFO)

A more complex version to encapsulate behavior:

.. code-block:: python

    import celery

    class Celery(celery.Celery):
        def on_configure(self):
            import raven
            from raven.contrib.celery import register_signal, register_logger_signal

            client = raven.Client()

            # register a custom filter to filter out duplicate logs
            register_logger_signal(client)

            # hook into the Celery error handler
            register_signal(client)

    app = Celery(__name__)
    app.config_from_object('django.conf:settings')
