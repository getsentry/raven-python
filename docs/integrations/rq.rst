RQ
==

Starting with RQ version 0.3.1, support for Sentry has been built in.

Usage
-----

RQ natively supports binding with Sentry by passing your ``SENTRY_DSN`` through ``rqworker``::

    $ rqworker --sentry-dsn="___DSN___"


Extended Setup
--------------

If you want to pass additional information, such as ``release``, you'll need to bind your
own instance of the Sentry ``Client``:

.. code-block:: python

    from raven import Client
    from raven.transport.http import HTTPTransport
    from rq.contrib.sentry import register_sentry

    client = Client('___DSN___', transport=HTTPTransport)
    register_sentry(client, worker)

Please see ``rq``'s documentation for more information:
http://python-rq.org/patterns/sentry/
