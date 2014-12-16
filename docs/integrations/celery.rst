Celery
======

.. code-block:: python

    from raven import Client
    from raven.contrib.celery import register_signal

    client = Client()
    register_signal(client)
