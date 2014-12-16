Configuring RQ
==============

Starting with RQ version 0.3.1, support for Sentry has been built in.

Usage
-----

The simplest way is passing your ``SENTRY_DSN`` through ``rqworker``::

    $ rqworker --sentry-dsn="http://public:secret@example.com/1"

Custom Client
-------------

It's possible to use a custom ``Client`` object and use your own worker process as an alternative to ``rqworker``.

Please see ``rq``'s documentation for more information: http://python-rq.org/patterns/sentry/
